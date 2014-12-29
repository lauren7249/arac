import argparse
import os
import requests
import datetime
import boto
import logging
import json
from itertools import islice
from dateutil import parser

from prime.prospects import models
from prime import create_app

from flask.ext.sqlalchemy import SQLAlchemy
from config import config

from boto.s3.key import Key
from boto.exception import S3ResponseError
from parser import lxml_parse_html
from convert import parse_html
from linkedin.scraper import process_request

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

app = create_app(os.getenv('AC_CONFIG', 'beta'))
db = SQLAlchemy(app)
session = db.session
s3conn = boto.connect_s3()
bucket = s3conn.get_bucket('arachid-results')

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
            extra['start_date'] = parser.parse(college.get('start_date', ''))
        except TypeError:
            pass

        try:
            extra['end_date'] = parser.parse(college.get('end_date', ''))
        except TypeError:
            try:
                extra['end_date'] = parser.parse(college.get('graduation_date', ''))
            except TypeError:
                pass

        new_education = models.Education(
            user = new_prospect.id,
            school_raw = college['college'],
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
            extra['start_date'] = parser.parse(e.get('start_date', ''))
        except TypeError:
            pass

        try:
            extra['end_date']   = parser.parse(e.get('end_date', ''))
        except TypeError:
            pass

        new_job = models.Job(
            user = new_prospect.id,
            title = e['title'],
            company_raw = e['company'],
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
    return True

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

def load_test_data():
    count = 0
    os.chdir("data")
    for filename in os.listdir(os.getcwd()):
        file = open(filename, 'r').read()
        content = json.loads(file)
        url = content.get("url")
        try:
            info =  parse_html(content.get("content"))
            if info_is_valid(info):
                create_prospect_from_info(info, url)
                logger.debug('successfully consumed {}th {}'.format(count, url))
        except Exception, e:
            import pdb
            pdb.set_trace()
            logger.error('could not get valid info for {}'.format(url))


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
                    prospect = session.query(models.Prospect).filter_by(s3_key=s3_key).first()

                    cleaned_id = info['linkedin_id']
                    try:
                        connections = info.get("connections")
                        prospect.connections = int(connections)
                    except Exception, e:
                        pass
                    prospect.people_raw = ";".join(info["people"])
                    prospect.linkedin_id = cleaned_id
                    prospect.updated = datetime.date.today()
                    #session.add(prospect)
                    info_jobs = filter(experience_is_valid, dedupe_dict(info.get('experiences', [])))
                    jobs = session.query(models.Job).filter_by(user=prospect.id)
                    for job in jobs:
                        for info_job in info_jobs:
                            company = info_job.get("company")
                            if company == job.company_raw:
                                try:
                                    start_date = parser.parse(info_job.get("start_date")).replace(tzinfo=None)
                                    job.start_date = start_date
                                except Exception, e:
                                    pass
                                try:
                                    end_date = parser.parse(info_job.get("end_date")).replace(tzinfo=None)
                                    job.end_date = end_date
                                except Exception, e:
                                    pass
                                job.location_raw = info_job.get("location_raw")
                                #session.add(job)

                    info_schools = filter(college_is_valid, dedupe_dict(info.get("schools", [])))
                    schools = session.query(models.Education).filter_by(user=prospect.id)
                    for school in schools:
                        for info_school in info_schools:
                            school_raw = info_school.get("college")
                            if school_raw == school.school_raw:
                                try:
                                    start_date = parser.parse(info_school.get("start_date")).replace(tzinfo=None)
                                    school.start_date = start_date
                                except Exception, e:
                                    pass
                                try:
                                    end_date = parser.parse(info_school.get("end_date")).replace(tzinfo=None)
                                    school.end_date = end_date
                                except Exception, e:
                                    try:
                                        end_date = parser.parse(info_school.get("graduation_date")).replace(tzinfo=None)
                                        job.end_date = end_date
                                    except Exception, e:
                                        pass
                                    pass
                                school.degree =info_school.get("degree")
                                #session.add(school)
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

            cleaned_id = info['linkedin_id']
            try:
                connections = info.get("connections")
                prospect.connections = int(connections)
            except Exception, e:
                pass
            people_raw = ";".join(info["people"])
            updated = datetime.date.today()

            new_prospect = models.Prospect(
                url=url,
                name = info['full_name'],
                linkedin_id = cleaned_id,
                location_raw = info.get('location'),
                industry_raw = info.get('industry'),
                s3_key = s3_key
            )
            new_prospect.updated = updated
            new_prospect.people_raw = people_raw
            new_prospect.connections = connections

            session.add(new_prospect)
            session.flush()

            for college in filter(college_is_valid, dedupe_dict(info.get("schools", []))):
                extra = {}
                try:
                    extra['start_date'] = parser.parse(college.get('start_date', ''))
                except TypeError:
                    pass

                try:
                    extra['end_date'] = parser.parse(college.get('end_date', ''))
                except TypeError:
                    try:
                        extra['end_date'] = parser.parse(college.get('graduation_date', ''))
                    except TypeError:
                        pass

                new_education = models.Education(
                    user = new_prospect.id,
                    school_raw = college['college'],
                    **extra
                )
                new_education.degree = college.get("degree")
                session.add(new_education)

            for e in filter(experience_is_valid, dedupe_dict(info.get('experiences', []))):
                extra = {}
                try:
                    extra['start_date'] = parser.parse(e.get('start_date', ''))
                except TypeError:
                    pass

                try:
                    extra['end_date']   = parser.parse(e.get('end_date', ''))
                except TypeError:
                    pass
                extra['location'] = e.get("location_raw")

                new_job = models.Job(
                    user = new_prospect.id,
                    title = e['title'],
                    company_raw = e['company'],
                    **extra
                )
                session.add(new_job)

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

