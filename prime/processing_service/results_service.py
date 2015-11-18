import hashlib
import logging
import time
import sys
import os
import boto
from boto.s3.key import Key

from requests import session
from service import Service, S3SavedRequest
from constants import SCRAPING_API_KEY, new_redis_host, new_redis_port, \
new_redis_password, new_redis_dbname

from prime.prospects.models import Prospect, School, Company, Job, Education


class ResultService(Service):

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.good_leads, self.bad_leads = data
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ResultService, self).__init__(*args, **kwargs)

    def _create_prospect(self, prospect):
        cleaned_id = info['linkedin_id'].strip()
        s3_key = url_to_key(url)
        if cleaned_id is None:
            self.logger.error("No linkedin id")
            return None
        exists = Prospect.query.filter(Prospect.linkedin_id == cleaned_id)
        if exists:
            return exists.first()

        today = datetime.date.today()

        data = {}
        data["skills"] = info.get("skills")
        data["groups"] = info.get("groups")
        data["projects"] = info.get("projects")
        data["people"] = info.get("people")
        data["interests"] = info.get("interests")
        data["causes"] = info.get("causes")
        data["organizations"] = info.get("organizations")

        new_prospect = Prospect(url=url,
            name = info['full_name'],
            linkedin_id = cleaned_id,
            location_raw = info.get('location'),
            industry_raw = info.get('industry'),
            image_url = info.get("image"),
            updated = today,
            connections = info.get("connections"),
            s3_key = s3_key)
        new_prospect.json = data
        session.add(new_prospect)
        session.commit()
        return new_prospect

    def _create_schools(self, new_prospect):
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
                        print "education updated for " + uu(new_prospect.url)

    def _create_jobs(self, propsect):
        pass


    def process(self):
        self.logger.info('Starting Process: %s', 'Result Service')
        for person in self.good_leads:
            import pdb
            pdb.set_trace()
        self.logger.info('Ending Process: %s', 'Result Service')
        return self.output
