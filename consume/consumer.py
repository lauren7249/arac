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
import requests
sys.path.append(".")
from prime.prospects import models
from prime import create_app

from flask.ext.sqlalchemy import SQLAlchemy
from config import config

from boto.s3.key import Key
from boto.exception import S3ResponseError
from parser import lxml_parse_html
from convert import parse_html
from sqlalchemy.orm import joinedload
from linkedin.scraper import process_request

from multiprocessing import Process, Queue

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

requests.packages.urllib3.disable_warnings()

def bootstrap_s3():
    s3conn = boto.connect_s3(os.environ["AWS_ACCESS_KEY_ID"], os.environ["AWS_SECRET_ACCESS_KEY"])
    bucket = s3conn.get_bucket('arachid-results')
    return bucket

try:
    app = create_app(os.getenv('AC_CONFIG', 'beta'))
    db = SQLAlchemy(app)
    session = db.session
except:
    from prime import db
    session = db.session

def prospect_exists(session, s3_key):
    if models.Prospect.s3_exists(session, s3_key):
        logger.debug('already processed s3_key {}'.format(s3_key))
        return True
    return False

def update_prospect(info, prospect, session=session):
    if prospect is None: return None
    today = datetime.date.today()
    data = prospect.json if prospect.json else {}
    data["skills"] = info.get("skills")
    data["groups"] = info.get("groups")
    data["projects"] = info.get("projects")
    data["people"] = info.get("people")
    session.query(models.Prospect).filter_by(id=prospect.id).update({
        "location_raw": info.get("location"),
        "industry_raw": info.get("industry"),
        "image_url": info.get("image"),
        "updated": today,
        "json": data
        })
    session.commit()
    return prospect

def create_prospect(info, url, session=session):
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

def create_schools(info, new_prospect, session=session):
    #if _session: session=_session
    if type(info) == list:
        info_schools = info
        new_prospect = session.query(models.Prospect).get(new_prospect.id)
    else:
        info_schools = filter(college_is_valid, dedupe_dict(info.get("schools", [])))
    for college in info_schools:
        insert_school(college, new_prospect, session=session)
    session.commit()
    return True

def create_jobs(info, new_prospect, session=session):
    #if _session: session = _session
    if type(info) == list:
        info_jobs = info
        new_prospect = session.query(models.Prospect).get(new_prospect.id)
    else:
        info_jobs = filter(experience_is_valid, dedupe_dict(info.get('experiences', [])))
    for e in info_jobs:
        insert_job(e, new_prospect, session=session)
    session.commit()
    return True

def update_jobs(info, new_prospect, session=session):
    jobs = info.get("experiences")
    new_jobs = []
    for info_job in jobs:
        new = True
        for job in new_prospect.jobs:

            if info_job.get("title") == job.title and info_job.get("company") == job.company.name:
                if convert_date(info_job.get("end_date")) != job.end_date  or convert_date(info_job.get("start_date")) != job.start_date or info_job.get("company_id") != job.company_linkedin_id or info_job.get("location") != job.location:
                    session.query(models.Job).filter_by(id=job.id).update({
                        "location": info_job.get("location"),
                        "start_date": convert_date(info_job.get("start_date")),
                        "end_date": convert_date(info_job.get("end_date")),
                        "company_linkedin_id": info_job.get("company_id")
                        })
                    print "job updated for " + new_prospect.url
                new = False
                break
        if new: new_jobs.append(info_job)

    for e in new_jobs:
        insert_job(e, new_prospect, session=session)
        print "job added for " + new_prospect.url
    session.commit()
    return True

def update_schools(info, new_prospect, session=session):
    schools = info.get("schools")
    new_schools = []
    for info_school in schools:
        new = True
        for school in new_prospect.schools:
            if info_school.get("degree") == school.degree and info_school.get("college") == school.school.name:
                if convert_date(info_school.get("start_date")) != school.start_date or convert_date(info_school.get("end_date")) != school.end_date or info_school.get("college_id") != school.school_linkedin_id:
                    session.query(models.Education).filter_by(id=school.id).update({
                        "start_date": convert_date(info_school.get("start_date")),
                        "end_date": convert_date(info_school.get("end_date")),
                        "school_linkedin_id": info_school.get("college_id")
                        })
                    print "education updated for " + new_prospect.url
                new = False
                break
        if new: new_schools.append(info_school)

    for e in new_schools:
        insert_school(e, new_prospect, session=session)
        print "education added for " + new_prospect.url
    session.commit()
    return True


def convert_date(date):
    try:
        return parser.parse(date, default=datetime.date(1979,1,1))
    except:
        return None

def insert_school(college, new_prospect, session=session):
    extra = {}
    extra['start_date'] = convert_date(college.get('start_date'))
    extra['end_date'] = convert_date(college.get('end_date'))
    if extra['end_date'] is None: extra['end_date'] = convert_date(college.get('graduation_date'))

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
        school_linkedin_id = college.get("college_id"),
        **extra
    )
    session.add(new_education)
    session.flush()

def insert_job(e, new_prospect, session=session):
    extra = {}
    extra['start_date'] = convert_date(e.get('start_date'))
    extra['end_date'] = convert_date(e.get('end_date'))

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
        company_linkedin_id=e.get("company_id"),
        **extra
    )
    session.add(new_job)
    session.flush()

def update_prospect_from_info(info, prospect, session=session):
    new_prospect = update_prospect(info, prospect, session=session)
    schools = update_schools(info, new_prospect, session=session)
    jobs = update_jobs(info, new_prospect, session=session)
    session.commit()
    return new_prospect

def get_friends_urls(prospect, session=session):
    lids = prospect.json.get("first_degree_linkedin_ids")
    urls = []

def create_prospect_from_info(info, url, session=session):
    new_prospect = create_prospect(info, url, session=session)
    schools = create_schools(info, new_prospect, session=session)
    jobs = create_jobs(info, new_prospect, session=session)
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
                    create_prospect_from_info(info, url, session=session)
                    logger.debug('successfully consumed {}th {}'.format(count, url))
                else:
                    logger.error('could not get valid info for {}'.format(url))

            except S3ResponseError:
                logger.error('couldn\'t get url {} from s3'.format(url))


def decode(s):
    if s:
        return unicode(s).encode("utf-8")
    return None

def parse_date(date):
    try:
        return parser.parse(date).replace(tzinfo=None)
    except:
        None


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
        file = open(filename.strip("\n"), 'r').read()
        data = json.loads(file)
        info = parse_html(data['content'])
        #info = get_info_for_url(filename.strip("\n"))
        if info_is_valid(info):
            linkedin_id = info.get("linkedin_id")
            info_jobs = filter(experience_is_valid, dedupe_dict(info.get('experiences', [])))
            for job in info_jobs:
                company = decode(job.get("company"))
                start_date = decode(job.get("start_date"))
                end_date = decode(job.get("end_date"))
                title = decode(job.get("title"))
                location = decode(job.get("location"))
                data = [linkedin_id, company, title, start_date, end_date,
                        location]
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


def dedupe_dict(ds):
    return map(dict, set(tuple(sorted(d.items())) for d in ds))

def url_to_key(url):
    return url.replace('/', '')

def get_info_for_url_live(url):
    headers ={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=headers, verify=False)
    response_text = response.content
    info = parse_html(response_text)
    return info


def get_info_for_url(url, bucket):
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


class LinkedinProcesser(object):

    __slots__ = ['filename', 'item_type', 'test', 'info', 'results', 's3_key']

    def __init__(self, filename, item_type="prospect", test=False, *args, **kwargs):
        self.filename = filename.strip("\n")
        self.s3_key = url_to_key(self.filename)
        self.test = test
        self.item_type = item_type
        self.results = self.run()

    def get_info(self, filename):
        if self.test:
            file = open(self.filename).read()
            data = json.loads(file)
            return parse_html(data['content'])
        else:
            return get_info_for_url(filename)

    def get_schools(self):
        schools = []
        info = self.info
        linkedin_id = info.get("linkedin_id")
        info_schools = filter(college_is_valid, dedupe_dict(info.get('schools', [])))
        for school in info_schools:
            school = decode(school.get("college"))
            start_date = parse_date(school.get("start_date"))
            end_date = parse_date(school.get("end_date"))
            degree = decode(school.get("degree"))
            description = decode(school.get("description"))
            school = [self.s3_key, linkedin_id, school, degree, start_date, end_date,
                    description]
            schools.append(school)
        return schools

    def get_jobs(self):
        jobs = []
        info = self.info
        linkedin_id = info.get("linkedin_id")
        info_jobs = filter(experience_is_valid, dedupe_dict(info.get('experiences', [])))
        for job in info_jobs:
            company = decode(job.get("company"))
            start_date = parse_date(job.get("start_date"))
            end_date = parse_date(job.get("end_date"))
            title = decode(job.get("title"))
            location = decode(job.get("location"))
            description = decode(job.get("description"))
            job = [self.s3_key, linkedin_id, company, title, location, description,
                    start_date, end_date]
            jobs.append(job)
        return jobs

    def get_prospects(self):
        info = self.info
        linkedin_id = info.get("linkedin_id")
        name = info.get("full_name")
        connections = info.get("connections")
        location = info.get("location")
        industry = info.get("industry")
        image = info.get("image")
        return [[self.s3_key, linkedin_id, name, connections, location, industry, image]]


    def run(self):
        self.info = self.get_info(self.filename)
        if self.item_type == 'prospect':
            return self.get_prospects()
        if self.item_type == 'schools':
            return self.get_schools()
        if self.item_type == 'jobs':
            return self.get_jobs()


class ConsumerMultiProcessing(object):

    __slots__ = ['input_file', 'output_file', 'processer', 'test', 'item_type',
            'workers', 'task_queue', 'done_queue']

    def __init__(self, input_file, output_file, processer, test=False, \
            item_type=None, workers=10, *args, **kwargs):
        self.input_file = input_file
        self.output_file = output_file
        self.processer = processer
        self.workers = workers
        self.test = test
        self.item_type = item_type
        self.task_queue = Queue()
        self.done_queue = Queue()

    def worker(self, input, output):
        for func, args in iter(input.get, 'STOP'):
            result = self.calculate(func, args)
            output.put(result)

    def calculate(self, func, args):
        result = func(*args)
        return result

    def run(self):
        start = time.time()
        os.chdir("data")
        count = 0
        writefile = open(self.output_file, "w+")
        a = csv.writer(writefile, delimiter='\t')
        filenames = ((self.processer, [f, self.item_type, self.test]) for f in open(self.input_file, "r"))
        for task in filenames:
            self.task_queue.put(task)
            count += 1

        for i in range(self.workers):
            Process(target=self.worker, args=(self.task_queue, self.done_queue)).start()

        for i in range(0, count):
            try:
                out = self.done_queue.get()
                if out.results:
                    a.writerows(out.results)
            except Exception, e:
                print e

        # Tell child processes to stop
        for i in range(self.workers):
            self.task_queue.put('STOP')

        print 'Total time elapsed:  %.10s seconds' % (time.time()-start)


def upgrade_from_file(url_file=None, start=0, end=-1):
    count = 0
    bucket = bootstrap_s3()
    with open(url_file, 'r') as f:
        for url in islice(f, start, end):
            try:
                count += 1
                update_prospect_from_url(url, bucket, session=session)
                logger.debug('successfully consumed {}th {}'.format(count, url))
            except Exception, e:
                session.rollback()
                logger.error('couldn\'t get url {} from s3, error: {}'.format(url, e))
                pass
            url = url.strip()

#This is so hacky its embarassing,but don't want to risk breaking the importer
#TODO Fix
def generate_prospect_from_url(url):
    url = url.strip()
    try:
        s3_key = url_to_key(url)
        info = get_info_for_url(url)
        if info_is_valid(info):
            if models.Prospect.s3_exists(session, s3_key):
                prospect = session.query(models.Prospect).filter_by(s3_key=s3_key).first()
                if prospect and prospect.jobs: return prospect
            new_prospect = create_prospect_from_info(info, url, session=session)
            session.commit()
            return new_prospect

    except S3ResponseError:
        return None

def update_prospect_from_url(url, bucket, session=session):
    url = url.strip()
    try:
        s3_key = url_to_key(url)
        info = get_info_for_url(url, bucket)
        if info_is_valid(info):
            prospect = session.query(models.Prospect).filter_by(s3_key=s3_key).options(joinedload(models.Prospect.schools).joinedload(models.Education.school), joinedload(models.Prospect.jobs).joinedload(models.Job.company)).first()
            new_prospect = update_prospect_from_info(info, prospect, session=session)
            session.commit()
            return new_prospect

    except S3ResponseError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('itemtype')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=None)
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--with-object', action='store_true')
    args = parser.parse_args()

    processer = LinkedinProcesser

    consumer = ConsumerMultiProcessing(args.input, args.output,
            processer, test=True, item_type=args.itemtype)
    consumer.run()

    """
    if args.test:
        load_test_data()
    elif:
    else:
        s3conn = boto.connect_s3()
        bucket = s3conn.get_bucket('arachid-results')
        process_from_file(url_flie=args.url_file, start=args.start, end=args.end)
    """

if __name__ == '__main__':
    main()

