import hashlib
import datetime
import logging
import time
import sys
import os
import boto
from boto.s3.key import Key

from prime.processing_service.service import Service, S3SavedRequest
from prime.processing_service.constants import SCRAPING_API_KEY, new_redis_host, new_redis_port, \
new_redis_password, new_redis_dbname

from prime.processing_service.helper import convert_date

from prime import create_app
from flask.ext.sqlalchemy import SQLAlchemy
from prime.prospects.models import Prospect, Job, Education, get_or_create
from prime.users.models import User
try:
    app = create_app(os.getenv('AC_CONFIG', 'development'))
    db = SQLAlchemy(app)
    session = db.session
except:
    from prime import db
    session = db.session


class ResultService(Service):

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.good_leads = data
        self.session = session
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ResultService, self).__init__(*args, **kwargs)

    def _create_or_update_prospect(self, person):
        data = person.get("linkedin_data")
        url = data.get("source_url")        
        cleaned_id = data.get('linkedin_id').strip()
        if cleaned_id is None:
            self.logger.error("No linkedin id")
            return None

        prospect = get_or_create(session, Prospect, linkedin_id=cleaned_id)

        today = datetime.date.today()
        new_data = {}
        new_data["skills"] = data.get("skills")
        new_data["groups"] = data.get("groups")
        new_data["projects"] = data.get("projects")
        new_data["people"] = data.get("people")
        new_data["interests"] = data.get("interests")
        new_data["causes"] = data.get("causes")
        new_data["organizations"] = data.get("organizations")

        connections = int(filter(lambda x: x.isdigit(), data.get("connections",
            0)))
        print person.keys()
        prospect.linkedin_url = url
        prospect.linkedin_name = data.get('full_name')
        prospect.linkedin_location_raw = data.get("location")
        prospect.linkedin_industry_raw = data.get("industry")
        prospect.linkedin_image_url = data.get("image")
        prospect.linkedin_connections = connections
        prospect.linkedin_headline = data.get("headline")
        prospect.updated = today
        prospect.linkedin_json = new_data
        latlng = person.get("location_coordinates",{}).get("latlng",[])
        if len(latlng)==2:
            prospect.lat = latlng[0]
            prospect.lng = latlng[1]
        prospect.phone = person.get("phone_number")
        prospect.age = person.get("age")
        prospect.college_grad = person.get("college_grad")
        prospect.gender = person.get("gender")
        prospect.indeed_salary = person.get("indeed_salary")
        prospect.glassdoor_salary = person.get("glassdoor_salary")
        prospect.dob_min_year = person.get("dob_min")
        prospect.dob_max_year = person.get("dob_max")
        prospect.email_addresses = person.get("email_addresses")
        self.session.add(prospect)
        self.session.commit()
        self.logger.info("Prospect updated")
        return prospect

    def _create_or_update_schools(self, new_prospect, person):
        data = person.get("linkedin_data")
        url = data.get("source_url")        
        schools = data.get("schools")
        new_schools = []
        for info_school in schools:
            new = True
            for school in new_prospect.schools:
                if info_school.get("degree") == school.degree and info_school.get("college") == school.school_name:
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

        new_education = Education(
                prospect = new_prospect,
                school_name = college.get("college"),
                degree = college.get("degree"),
                #TODO do we still need this?
                #school_linkedin_id = college.get("college_id"),
                **extra
                )
        self.session.add(new_education)
        self.session.flush()
        self.logger.info("Education added: {}".format(college.get("college")))

    def _create_or_update_jobs(self, new_prospect, person):
        data = person.get("linkedin_data")
        url = data.get("source_url")        
        jobs = data.get("experiences")
        new_jobs = []
        for info_job in jobs:
            new = True
            for job in new_prospect.jobs:
                if info_job.get("title") == job.title and \
                info_job.get("company") == job.company_name and \
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

        new_job = Job(
            prospect = new_prospect,
            title = job.get('title'),
            company_name=job.get("company"),
            **extra
        )
        self.session.add(new_job)
        self.session.flush()
        self.logger.info("Job added: {}".format(job.get("company")))

    def _get_user(self):
        user = session.query(User).filter_by(email=self.user_email).first()
        return user

    def process(self):
        self.logger.info('Starting Process: %s', 'Result Service')
        user = self._get_user()
        if user is None:
            self.logger.error("No user found for %s", self.user_email)
            return None
        for person in self.good_leads:
            prospect = self._create_or_update_prospect(person)
            self._create_or_update_schools(prospect, person)
            self._create_or_update_jobs(prospect, person)
        self.logger.info('Ending Process: %s', 'Result Service')
        return self.output
