import logging
import hashlib
import boto
import lxml.html
import re
import dateutil
import requests
from requests import HTTPError
from boto.s3.key import Key

from service import Service, S3SavedRequest
from bing_service import BingService
from constants import GLOBAL_HEADERS
from services.linkedin_query_api import get_company

class LinkedinCompanyService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be existig data enriched with linkedin company info
    """

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(LinkedinCompanyService, self).__init__(*args, **kwargs)

    def process(self):
        self.logger.info('Starting Process: %s', 'Linkedin Company Service')
        for person in self.data:
            current_job = self._current_job(person)
            if current_job:
                request = LinkedinCompanyRequest(current_job)
                data = request.process()
                if data:
                    #TODO: add more fields
                    person.update({"company_website": data.get("website")})
                    person.update({"company_industry": data.get("industry")})
                    person.update({"company_headquarters": data.get("hq")})
            self.output.append(person)
        self.logger.info('Ending Process: %s', 'Linkedin Company Service')
        return self.output

class LinkedinCompanyRequest(S3SavedRequest):

    """
    Given a dict of company attributes, this will return the linkedin company page info
    """

    def __init__(self, company):
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.urls = []
        self.index = 0
        self.company_name = company.get("company")
        self.company_linkedin_url = company.get("company_linkedin_url")
        self.company_id = company.get("company_id")
        if self.company_linkedin_url:
            self.urls.append(self.company_linkedin_url)       
        super(LinkedinCompanyRequest, self).__init__()

    def _get_urls(self):
        if self.urls or not self.company_name:
            return
        bing = BingService(self.company_name, "linkedin_company")
        self.urls = bing.process()

    def has_next_url(self):
        self._get_urls()
        if self.index < len(self.urls):
            return True
        return False

    def process_next(self):
        if self.has_next_url():
            self.url = self.urls[self.index]
            self.index +=1
            self.logger.info('Linkedin Company Request: %s', 'Starting')
            info = get_company(url=self.url)
            return info
        return {}

    def process(self):
        info = {}
        if self.company_id:
            info = get_company(linkedin_id=self.company_id)
            if info:
                self.logger.info("got Linkedin Company info from linkedin id")
                return info
        while not info and self.has_next_url():
            info = self.process_next()
            if info: 
                return info
        return info




