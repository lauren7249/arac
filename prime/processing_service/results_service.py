
import hashlib
import datetime
import logging
import time
import sys
import os
import boto
import json
from boto.s3.key import Key

from prime.processing_service.service import Service, S3SavedRequest
from prime.processing_service.constants import SOCIAL_DOMAINS

from prime.processing_service.helper import convert_date, uu
from prime import create_app
from flask.ext.sqlalchemy import SQLAlchemy
from prime.users.models import ClientProspect
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

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
        self.good_leads = data
        self.session = session
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ResultService, self).__init__(*args, **kwargs)

    def _create_or_update_client_prospect(self, prospect, user, profile):
        if not user or not prospect:
            return None
        client_prospect = get_or_create(self.session, ClientProspect, prospect_id = prospect.id, user_id =user.user_id)
        client_prospect.extended = profile.get("extended")
        client_prospect.referrers = profile.get("referrers")
        client_prospect.lead_score = profile.get("lead_score")
        client_prospect.stars = profile.get("stars")
        client_prospect.common_schools = profile.get("common_schools")
        client_prospect.updated = datetime.datetime.today()  
        self.session.add(client_prospect)
        self.session.commit()
        self.logger.info("client prospect updated")        
        return client_prospect

    def _create_or_update_prospect(self, profile):
        if not profile:
            self.logger.error("No person")
            return None            
        if profile.get('linkedin_id') is None:
            self.logger.error("No linkedin id")
            return None
        prospect = get_or_create(self.session, Prospect, linkedin_id=profile.get('linkedin_id').strip())
        for key, value in profile.iteritems():
            if hasattr(Prospect, key):
                setattr(prospect, key, value)      
        prospect.updated = datetime.datetime.today()  
        self.session.add(prospect)
        self.session.commit()
        self.logger.info("Prospect updated")
        return prospect

    def _create_or_update_schools(self, new_prospect, profile):     
        schools = profile.get("schools_json",[])
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
                    self.logger.info("Education updated: {}".format(uu(info_school.get("college"))))
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
        self.logger.info("Education added: {}".format(uu(college.get("college"))))

    def _create_or_update_jobs(self, new_prospect, profile):      
        jobs = profile.get("jobs_json",[])
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
                    self.logger.info("Job updated: {}".format(uu(info_job.get("company"))))
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
        self.logger.info("Job added: {}".format(uu(job.get("company"))))

    def _get_user(self):
        user = session.query(User).filter_by(email=self.client_data.get("email")).first()
        return user

    def multiprocess(self):
        return self.process()
        
    def process(self):
        self.logger.info('Starting Process: %s', 'Result Service')
        user = self._get_user()
        if user is None:
            self.logger.error("No user found for %s", self.client_data.get("email"))
            return None
        for profile in self.good_leads:
            prospect = self._create_or_update_prospect(profile)
            if not prospect:
                self.logger.error("no prospect %s", json.dumps(profile))
                continue
            self._create_or_update_schools(prospect, profile)
            self._create_or_update_jobs(prospect, profile)
            client_prospect = self._create_or_update_client_prospect(prospect, user, profile)
            if not client_prospect:
                self.logger.error("no client prospect")
                continue
            self.output.append(client_prospect.to_json())
        if user:
            self.logger.info("Stats: %s", json.dumps(user.build_statistics()))
        else:
            self.logger.error("NO USER!")
        self.logger.info('Ending Process: %s', 'Result Service')
        return self.output
