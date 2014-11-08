import argparse
import boto
import logging
import models
import json
from itertools import islice
from dateutil import parser

from boto.s3.key import Key
from boto.exception import S3ResponseError
from parser import lxml_parse_html
from convert import parse_html

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

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

def process_from_file(url_file=None, start=0, end=-1):
    session = models.Session()
    count = 0
    with open(url_file, 'r') as f:
        for url in islice(f, start, end):
            url = url.strip()
            try:
                count += 1
                s3_key = url_to_key(url)

                if models.Prospect.s3_exists(session, s3_key):
                    logger.debug('already processed s3_key {}'.format(
                        s3_key
                    ))
                    continue

                info = get_info_for_url(url)
                if info_is_valid(info):
                    cleaned_id = info['linkedin_id'].strip()

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
                            degree = college.get("degree")
                            **extra
                        )
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

                        new_job = models.Job(
                            user = new_prospect.id,
                            title = e['title'],
                            company_raw = e['company'],
                            **extra
                        )
                        session.add(new_job)

                    session.commit()

                    logger.debug('successfully consumed {}th {}'.format(count, url))
                else:
                    logger.error('could not get valid info for {}'.format(url))

            except S3ResponseError:
                logger.error('couldn\'t get url {} from s3'.format(url))


def upgrade_from_file(url_file=None, start=0, end=-1):
    session = models.Session()
    count = 0
    with open(url_file, 'r') as f:
        for url in islice(f, start, end):
            url = url.strip()
            count += 1
            s3_key = url_to_key(url)
            prospect = session.query(models.Prospect).filter_by(s3_key=s3_key).first()
            info = get_info_for_url(url)
            if info_is_valid(info):
                prospect.linkedin_id = info.get("linkedin_id")
                session.add(prospect)
                info_jobs = filter(experience_is_valid, dedupe_dict(info.get('experiences', [])))
                jobs = session.query(models.Job).filter_by(user=prospect.id)
                for job in jobs:
                    for info_job in info_jobs:
                        company = info_job.find("company")
                        if company == job.company_raw:
                            job.start_date = info_job.get("start_date")
                            job.end_date = info_job.get("end_date")
                            job.location_raw = info_job.get("location_raw")
                            session.add(job)

                info_schools = filter(college_is_valid, dedupe_dict(info.get("schools", [])))
                schools = session.query(models.Education).filter(user=prospect.id)
                for school in schools:
                    for info_school in info_schools:
                        school_raw = info_school.find("schools")
                        if school_raw == school.school_raw:
                            school.start_date = info_school.get("start_date")
                            school.end_date = info_school.get("end_date")
                            school.degree =info_school.get("degree")
                            session.add(school)
            session.commit()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url_file')
    parser.add_argument('--start', type=int, default=0)
    parser.add_argument('--end', type=int, default=None)

    args = parser.parse_args()
    process_from_file(url_flie=args.url_file, start=args.start, end=args.end)

if __name__ == '__main__':
    main()

