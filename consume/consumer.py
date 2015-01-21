import argparse
import time
import sys
import csv
import os
import requests
import datetime
import boto
import logging
import json
from itertools import islice
from dateutil import parser

sys.path.append(".")
from prime.prospects import models
from prime import create_app

from flask.ext.sqlalchemy import SQLAlchemy
from config import config

from boto.s3.key import Key
from boto.exception import S3ResponseError
from parser import lxml_parse_html
from convert import parse_html
from linkedin.scraper import process_request

from multiprocessing import Process, Queue

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

s3conn = boto.connect_s3("AKIAIWG5K3XHEMEN3MNA", "luf+RyH15uxfq05BlI9xsx8NBeerRB2yrxLyVFJd")
bucket = s3conn.get_bucket('arachid-results')

try:
    app = create_app(os.getenv('AC_CONFIG', 'beta'))
    db = SQLAlchemy(app)
    session = db.session
except:
    from prime import db
    session = db.session

def dedupe_dict(ds):
    return map(dict, set(tuple(sorted(d.items())) for d in ds))

def url_to_key(url):
    return url.replace('/', '')

def get_info_for_url(url):
    key = Key(bucket)
    key.key = url_to_key(url)
    data = json.loads(key.get_contents_as_string())
    info = parse_html(data['content'])
    return info

def college_is_valid(e):
    return bool(e.get('college'))

def experience_is_valid(e):
    return bool(e.get('company'))


def info_is_valid(info):
    return info.get('full_name') and \
           info.get('linkedin_id')

def prospect_exists(session, s3_key):
    if models.Prospect.s3_exists(session, s3_key):
        logger.debug('already processed s3_key {}'.format(s3_key))
        return True
    return False

def create_prospect(info, url):
    cleaned_id = info['linkedin_id'].strip()
    s3_key = url_to_key(url)
    new_prospect = models.Prospect(
        url=url,
        name         = info['full_name'],
        linkedin_id  = cleaned_id,
        location_raw = info.get('location'),
        industry_raw = info.get('industry'),
        s3_key       = s3_key
    )

    session.add(new_prospect)
    session.flush()
    return new_prospect

def create_schools(info, new_prospect):
    for college in filter(college_is_valid, dedupe_dict(info.get("schools", []))):
        extra = {}
        try:
            extra['start_date'] = parser.parse(college.get('start_date')).replace(tzinfo=None)
        except:
            pass

        try:
            extra['end_date'] = parser.parse(college.get('end_date')).replace(tzinfo=None)
        except:
            try:
                extra['end_date'] = parser.parse(college.get('graduation_date')).replace(tzinfo=None)
            except:
                pass

        school = session.query(models.School).filter_by(name=college['college']).first()
        if not school:
            school = models.School(
                    name=college['college']
                    )
            session.add(school)
            session.flush()

        new_education = models.Education(
            prospect = new_prospect,
            school = school,
            degree = college.get("degree"),
            **extra
        )
        session.add(new_education)
        session.flush()
    return True

def create_jobs(info, new_prospect):
    for e in filter(experience_is_valid, dedupe_dict(info.get('experiences', []))):
        extra = {}
        try:
            extra['start_date'] = parser.parse(e.get('start_date')).replace(tzinfo=None)
        except:
            pass

        try:
            extra['end_date']   = parser.parse(e.get('end_date')).replace(tzinfo=None)
        except:
            pass

        company = session.query(models.Company).filter_by(name=e['company']).first()
        if not company:
            company = models.Company(
                    name=e['company']
                    )
            session.add(company)
            session.flush()

        new_job = models.Job(
            prospect = new_prospect,
            title = e['title'],
            company=company,
            **extra
        )
        session.add(new_job)
        session.flush()
    return True

def create_prospect_from_info(info, url):
    new_prospect = create_prospect(info, url)
    schools = create_schools(info, new_prospect)
    jobs = create_jobs(info, new_prospect)
    session.commit()
    return new_prospect

def process_from_file(url_file=None, start=0, end=-1):
    count = 0
    with open(url_file, 'r') as f:
        for url in islice(f, start, end):
            url = url.strip()
            try:
                count += 1
                s3_key = url_to_key(url)
                if prospect_exists(session, s3_key):
                    continue
                info = get_info_for_url(url)
                if info_is_valid(info):
                    create_prospect_from_info(info, url)
                    logger.debug('successfully consumed {}th {}'.format(count, url))
                else:
                    logger.error('could not get valid info for {}'.format(url))

            except S3ResponseError:
                logger.error('couldn\'t get url {} from s3'.format(url))


def decode(s):
    if s:
        return unicode(s).encode("utf-8")
    return None


def worker(input, output):
    for func, args in iter(input.get, 'STOP'):
        result = calculate(func, args)
        output.put(result)

# Function 'calculate' is a general function allowing any function/args to be passed
# from a Task-List/Queue
def calculate(func, args):
    result = func(*args)
    return result


def process_test_data(filename):
    all_data = []
    try:
        #file = open(filename.strip("\n"), 'r').read()
        info = get_info_for_url(filename.strip("\n"))
        if info_is_valid(info):
            linkedin_id = info.get("linkedin_id")
            info_jobs = filter(experience_is_valid, dedupe_dict(info.get('experiences', [])))
            for job in info_jobs:
                company = decode(job.get("company"))
                start_date = decode(job.get("start_date"))
                end_date = decode(job.get("end_date"))
                title = decode(job.get("title"))
                data = [linkedin_id, company, title, start_date, end_date]
                all_data.append(data)
        return all_data
    except Exception, e:
        print e
        pass

def load_test_data():
    start = time.time()
    task_queue = Queue()
    done_queue = Queue()
    os.chdir("data")
    count = 0
    with open("testing2.txt", 'w+') as f:
        a = csv.writer(f, delimiter='\t')
        filenames = ((process_test_data, [f]) for f in open("/home/ubuntu/remaining_oct30.txt", "r"))
        for task in filenames:
            task_queue.put(task)
            count += 1

        for i in range(100):
            Process(target=worker, args=(task_queue, done_queue)).start()

        # Get results
        for i in range(0, count):
            try:
                out = done_queue.get()
                if out:
                    for item in out:
                        a.writerow(item) # write to output file
            except:
                pass

        # Tell child processes to stop
        for i in range(100):
            task_queue.put('STOP')

        print 'Total time elapsed:  %.10s seconds' % (time.time()-start)




def upgrade_from_file(url_file=None, start=0, end=-1):
    count = 0
    with open(url_file, 'r') as f:
        for url in islice(f, start, end):
            url = url.strip()
            try:
                count += 1
                s3_key = url_to_key(url)
                info = get_info_for_url(url)
                if info_is_valid(info):
                    info_jobs = filter(experience_is_valid, dedupe_dict(info.get('experiences', [])))
                    for info_job in info_jobs:
                        company = info_job.get("company")
                        if company == job.company.name:
                            print info_job.get("location")
                            job.location = info_job.get("location")
                    session.commit()
                    logger.debug('successfully consumed {}th {}'.format(count, url))
                else:
                    logger.error('could not get valid info for {}'.format(url))

            except Exception, e:
                session.rollback()
                logger.error('couldn\'t get url {} from s3, error: {}'.format(url, e))
                pass

#This is so hacky its embarassing,but don't want to risk breaking the importer
#TODO Fix
def generate_prospect_from_url(url):
    url = url.strip()
    try:
        s3_key = url_to_key(url)
        info = get_info_for_url(url)
        if info_is_valid(info):
            if models.Prospect.s3_exists(session, s3_key):
                return session.query(models.Prospect).filter_by(s3_key=s3_key).first()
            new_prospect = create_prospect_from_info(info, url)
            session.commit()
            return new_prospect

    except S3ResponseError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url_file')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=None)
    parser.add_argument('--test', action='store_true')

    args = parser.parse_args()
    if args.test:
        load_test_data()
    else:
        s3conn = boto.connect_s3()
        bucket = s3conn.get_bucket('arachid-results')
        process_from_file(url_flie=args.url_file, start=args.start, end=args.end)

if __name__ == '__main__':
    main()

