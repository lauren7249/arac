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
from prime.processing_service.bloomberg_service import BloombergPhoneService

class PhoneService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be existig data enriched with phone numbers
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(PhoneService, self).__init__(*args, **kwargs)

    def dispatch(self):
        pass

    def process(self):
        self.service = BloombergPhoneService(self.user_email, self.user_linkedin_url, self.data)
        self.data = self.service.process()
        return self.data
