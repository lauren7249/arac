import logging
import hashlib
import boto
import lxml.html
import re
import dateutil
import requests
from requests import HTTPError
from boto.s3.key import Key
import multiprocessing
from service import Service, S3SavedRequest
from constants import GLOBAL_HEADERS
from linkedin_company_service import LinkedinCompanyService
from bloomberg_service import BloombergPhoneService
from clearbit_service_webhooks import ClearbitPhoneService
from mapquest_request import MapQuestRequest
from person_request import PersonRequest

def wrapper(person, favor_mapquest=False):
    if not person:
        return person
    if person.get("phone_number") and not favor_mapquest:
        return person
    linkedin_data = person.get("linkedin_data",{})
    current_job = PersonRequest()._current_job(person)
    if not current_job or not current_job.get("company"):
        return person
    location = MapQuestRequest(linkedin_data.get("location")).process()
    latlng = location.get("latlng") if location else None
    business_service = MapQuestRequest(current_job.get("company"))
    business = business_service.get_business(latlng=latlng, website=person.get("company_website"))
    person.update(business) 
    return person

class PhoneService(Service):
    """
    Expected input is JSON with linkedin profiles
    Output is going to be existig data enriched with phone numbers
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(PhoneService, self).__init__(*args, **kwargs)
        self.client_data = client_data
        self.data = data
        self.output = []
        self.wrapper = wrapper
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def multiprocess(self):
        self.logstart()
        self.service = LinkedinCompanyService(self.client_data, self.data)
        self.data = self.service.multiprocess()        
        self.service = BloombergPhoneService(self.client_data, self.data)
        self.data = self.service.multiprocess()
        self.pool = multiprocessing.Pool(self.pool_size)
        self.output = self.pool.map(self.wrapper, self.data)
        self.pool.close()
        self.pool.join()
        self.service = ClearbitPhoneService(self.client_data, self.output)
        self.output = self.service.multiprocess()
        self.logend()
        return self.output

    def process(self, favor_mapquest=False):
        self.logstart()
        self.service = LinkedinCompanyService(self.client_data, self.data)
        self.data = self.service.process()          
        self.service = BloombergPhoneService(self.client_data, self.data)
        self.data = self.service.process()
        for person in self.data:
            person = wrapper(person, favor_mapquest=favor_mapquest)
            self.output.append(person)
        self.service = ClearbitPhoneService(self.client_data, self.output)
        self.output = self.service.process()
        self.logend()
        return self.output
