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
from constants import GLOBAL_HEADERS
from bloomberg_service import BloombergPhoneService
from clearbit_service_webhooks import ClearbitPhoneService
from mapquest_service import MapQuestRequest

class PhoneService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existig data enriched with phone numbers
    """

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(PhoneService, self).__init__(*args, **kwargs)

    def process(self, favor_mapquest=False, favor_clearbit=False):
        self.logger.info("PhoneNumber Service %s", "Starting")
        self.service = BloombergPhoneService(self.client_data, self.data)
        self.data = self.service.process()
        for person in self.data:
            if person.get("phone_number") and not favor_mapquest:
                self.logger.info("PhoneNumber service: already has phone number %s", person.get("phone_number"))
                self.output.append(person)
                continue
            linkedin_data = person.get("linkedin_data",{})
            current_job = self._current_job(person)
            if not current_job or not current_job.get("company"):
                self.logger.info("PhoneNumber service: no current job or company")
                self.output.append(person)
                continue
            business_service = MapQuestRequest(current_job.get("company"))
            location_service = MapQuestRequest(linkedin_data.get("location"))
            latlng = location_service.process().get("latlng")
            business = business_service.get_business(latlng=latlng, website=person.get("company_website"))
            person.update(business)
            self.output.append(person)
        self.service = ClearbitPhoneService(self.client_data, self.output)
        self.output = self.service.process(overwrite=favor_clearbit)
        return self.output
