import re
import os
import sys
import argparse
from dateutil import parser
import urlparse
import logging
sys.path.append(".")
from prime.prospects.models import Prospect, Job, Education
from prime import create_app

from flask.ext.sqlalchemy import SQLAlchemy
from config import config
from prime import create_app

from consume.consumer import get_info_for_url, experience_is_valid,\
        dedupe_dict, college_is_valid, info_is_valid, create_schools,\
        create_jobs

app = create_app(os.getenv('AC_CONFIG', 'beta'))
db = SQLAlchemy(app)
session = db.session

def make_hashable(d):
    return (frozenset(x.iteritems()) for x in d)

def merge_jobs(jobs, info_jobs, info):
    found_jobs = []
    for i, info_job in enumerate(info_jobs):
        found = False
        for job in jobs:
            if job.company.name == info_job.get("company") and job.title == info_job.get("title"):
                extra = {}
                extra['title'] = info_job.get("title")
                if info_job.get("start_date"):
                    extra['start_date'] = parser.parse(info_job.get("start_date")).replace(tzinfo=None)
                if info_job.get("end_date"):
                    extra['end_date'] =  parser.parse(info_job.get("end_date")).replace(tzinfo=None)
                extra['location'] = info_job.get("location")
                #extra['description'] = info_job.get("description")
                session.query(Job).filter_by(id=job.id).update(extra)
                session.commit()
                found_jobs.append(info_job)
    missed_jobs_tuples = set(make_hashable(info_jobs))\
            .difference(make_hashable(found_jobs))

    missed_jobs = [dict(x) for x in missed_jobs_tuples]
    if len(missed_jobs) > 0:
        create_jobs(missed_jobs, job.prospect)
    return len(missed_jobs)


def merge_schools(schools, info_schools, info):
    found_educations = []
    for i, info_school in enumerate(info_schools):
        for education in schools:
            if education.school.name == info_school.get("college"):
                extra = {}
                extra['degree'] = info_school.get("degree")
                if info_school.get("start_date"):
                    extra['start_date'] = parser.parse(info_school.get("start_date")).replace(tzinfo=None)
                if info_school.get("end_date"):
                    extra['end_date'] =  parser.parse(info_school.get("end_date")).replace(tzinfo=None)
                #extra['description'] = info_school.get("description")
                session.query(Education).filter_by(id=education.id).update(extra)
                session.commit()
                found_educations.append(info_school)
    missed_educations_tuples = set(make_hashable(info_schools))\
            .difference(make_hashable(found_educations))

    missed_schools = [dict(x) for x in missed_educations_tuples]
    if len(missed_schools) > 0:
        create_schools(info_schools, education.prospect)
    return len(missed_schools)

def update_information(prospect):
    info = get_info_for_url(prospect.url)
    if info_is_valid(info):
        info_jobs = filter(experience_is_valid, dedupe_dict(info.get('experiences', [])))
        info_schools = filter(college_is_valid, dedupe_dict(info.get('schools', [])))
        created_jobs = merge_jobs(prospect.jobs, info_jobs, info)
        created_schools = merge_schools(prospect.schools, info_schools, info)
        old_json = prospect.json if prospect.json else {}
        old_json['groups'] = info.get("groups")
        old_json['projects'] = info.get("projects")
    return created_jobs, created_schools


def update_prospect(linkedin_id):
    NEW_EDUCATIONS = 0
    NEW_JOBS = 0
    prospect = session.query(Prospect).filter_by(linkedin_id=linkedin_id).first()
    new_jobs, new_educations = update_information(prospect)
    NEW_JOBS += new_jobs
    NEW_EDUCATIONS += new_educations
    company_ids = [job.company_id for job in prospect.jobs]
    school_ids = tuple([school.school_id for school in prospect.schools])
    company_prospects = session.query(Prospect).join(Job).filter(Job.company_id.in_(\
            company_ids)).distinct(Prospect.id).all()
    school_prospects = session.query(Prospect).join(Education)\
            .filter(Education.school_id.in_(school_ids)).distinct(Prospect.id).all()

    for school_prospect in school_prospects:
        if prospect.id != school_prospect.id:
            new_jobs, new_educations = update_information(school_prospect)
            NEW_JOBS += new_jobs
            NEW_EDUCATIONS += new_educations

    for company_prospect in company_prospects:
        if prospect.id != company_prospect.id:
            new_jobs, new_educations = update_information(company_prospect)
            NEW_JOBS += new_jobs
            NEW_EDUCATIONS += new_educations

    print "{} Schools created and {} jobs created".format(NEW_JOBS,
            NEW_EDUCATIONS)

if __name__ == '__main__':
    aparser = argparse.ArgumentParser()
    aparser.add_argument('linkedin_id')
    args = aparser.parse_args()
    update_prospect(args.linkedin_id)
