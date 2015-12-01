import hashlib
import datetime
import logging
import time
import sys
import os
import boto
from boto.s3.key import Key

from service import Service, S3SavedRequest
from constants import SCRAPING_API_KEY, new_redis_host, new_redis_port, \
new_redis_password, new_redis_dbname

from helper import convert_date

from prime import create_app
from flask.ext.sqlalchemy import SQLAlchemy
from prime.prospects.models import Prospect, School, Company, Job, Education
try:
    app = create_app(os.getenv('AC_CONFIG', 'development'))
    db = SQLAlchemy(app)
    session = db.session
except:
    from prime import db
    session = db.session


class ResultService(Service):

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.good_leads, self.bad_leads = data
        self.session = session
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ResultService, self).__init__(*args, **kwargs)

    def _create_prospect(self, data, url):
        cleaned_id = data['linkedin_id'].strip()
        s3_key = url.replace('/', '')
        if cleaned_id is None:
            self.logger.error("No linkedin id")
            return None
        exists = self.session.query(Prospect).filter(Prospect.linkedin_id == \
                cleaned_id).first()
        if exists:
            return exists

        today = datetime.date.today()
        new_data = {}
        new_data["skills"] = data.get("skills")
        new_data["groups"] = data.get("groups")
        new_data["projects"] = data.get("projects")
        new_data["people"] = data.get("people")
        new_data["interests"] = data.get("interests")
        new_data["causes"] = data.get("causes")
        new_data["organizations"] = data.get("organizations")

        new_prospect = Prospect(url=url,
            name = data['full_name'],
            linkedin_id = cleaned_id,
            location_raw = data.get('location'),
            industry_raw = data.get('industry'),
            image_url = data.get("image"),
            updated = today,
            connections = data.get("connections"),
            s3_key = s3_key)
        new_prospect.json = new_data
        self.session.add(new_prospect)
        self.session.commit()
        return new_prospect

    def _create_or_update_schools(self, new_prospect, data):
        schools = data.get("schools")
        new_schools = []
        for info_school in schools:
            new = True
            for school in new_prospect.schools:
                if info_school.get("degree") == school.degree and info_school.get("college") == school.school.name:
                    self.session.query(Education).filter_by(id=school.id).update({
                        "start_date": convert_date(info_school.get("start_date")),
                        #"school_linkedin_id": info_school.get("college_id")
                        "end_date": convert_date(info_school.get("end_date"))
                        })
                    self.logger.info("Education updated: {}".format(info_school.get("college")))
                    new = False
                    break
            if new:
                new_schools.append(info_school)
        for school in new_schools:
            self._insert_school(new_prospect, school)
        return True


    def _insert_school(self, new_prospect, college):
        extra = {}
        extra['start_date'] = convert_date(college.get('start_date'))
        extra['end_date'] = convert_date(college.get('end_date'))
        if extra['end_date'] is None: extra['end_date'] = convert_date(college.get('graduation_date'))

        school = self.session.query(School).filter_by(name=college['college']).first()
        if not school:
            school = School(
                    name=college['college']
                    )
            self.session.add(school)
            self.session.flush()

        new_education = Education(
                prospect = new_prospect,
                school = school,
                degree = college.get("degree"),
                #TODO do we still need this?
                #school_linkedin_id = college.get("college_id"),
                **extra
                )
        self.session.add(new_education)
        self.session.flush()
        self.logger.info("Education added: {}".format(college.get("college")))

    def _create_or_update_jobs(self, new_prospect, data):
        jobs = data.get("experiences")
        new_jobs = []
        for info_job in jobs:
            new = True
            for job in new_prospect.jobs:
                if info_job.get("title") == job.title and \
                info_job.get("company") == job.company.name and \
                convert_date(info_job.get("start_date")) == job.start_date:
                    self.session.query(Job).filter_by(id=job.id).update({
                        "location": info_job.get("location"),
                        "start_date": convert_date(info_job.get("start_date")),
                        #"company_linkedin_id": info_job.get("company_id")
                        "end_date": convert_date(info_job.get("end_date"))
                        })
                    self.logger.info("Job updated: {}".format(info_job.get("company")))
                    new = False
                    break
            if new:
                new_jobs.append(info_job)

        for job in new_jobs:
            self._insert_job(new_prospect, job)
        self.session.commit()
        return True

    def _insert_job(self, new_prospect, job):
        extra = {}
        extra['start_date'] = convert_date(job.get('start_date'))
        extra['end_date'] = convert_date(job.get('end_date'))

        company = self.session.query(Company).filter_by(name=job['company']).first()
        if not company:
            company = Company(
                    name=job['company']
                    )
            self.session.add(company)
            self.session.flush()

        new_job = Job(
            prospect = new_prospect,
            title = job['title'],
            company=company,
            #TODO do we still need this?
            #company_linkedin_id=job.get("company_id"),
            **extra
        )
        self.session.add(new_job)
        self.session.flush()
        self.logger.info("Job added: {}".format(job.get("company")))


    def process(self):
        self.logger.info('Starting Process: %s', 'Result Service')
        for person in self.good_leads:
            data = person.get("linkedin_data")
            url = self._get_linkedin_url(person)
            prospect = self._create_prospect(data, url)
            self._create_or_update_schools(prospect, data)
            self._create_or_update_jobs(prospect, data)
        self.logger.info('Ending Process: %s', 'Result Service')
        return self.output
