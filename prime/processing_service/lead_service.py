import clearbit
import logging
import hashlib
import boto

from requests import HTTPError
from boto.s3.key import Key

from service import Service, S3SavedRequest
from linkedin_service import LinkedinRequest

class LeadService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts and Linkedin IDs via PIPL
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.location = None
        self.jobs = []
        self.schools = []
        self.salary_limit = 50000
        self.good_leads = []
        self.bad_leads = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _filter_same_locations(self, person):
        if self.location == person.get("location_raw"):
            return True
        return False

    def _filter_salaries(self, person):
        salary = max(person.get("glassdoor_salary", 0), \
                person.get("indeed_salary", 0))
        if salary > self.salary_limit:
            return True
        return False

    def _get_self_jobs_and_schools(self):
        person = LinkedinRequest(self.user_linkedin_url, {}).process()
        self.jobs = person.get("experiences")
        self.schools = person.get("schools")
        self.location = person.get("location_raw")

    def process(self):
        self.logger.info('Starting Process: %s', 'Lead Service')
        self._get_self_jobs_and_schools()
        for person in self.data:
            salary = self._filter_salaries(person)
            location = self._filter_same_locations(person)
            if salary and location:
                self.good_leads.append(person)
            else:
                self.bad_leads.append(person)
        self.logger.info('Good Leads: %s', len(self.good_leads))
        self.logger.info('Bad Leads: %s', len(self.bad_leads))
        self.logger.info('Ending Process: %s', 'Lead Service')
        return self.good_leads, self.bad_leads
