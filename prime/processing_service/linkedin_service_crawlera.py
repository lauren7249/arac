import hashlib
import logging
import time
import sys
import os
import boto
from boto.s3.key import Key
import json
import requests
from service import Service
from saved_request import S3SavedRequest

class LinkedinService(Service):

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(LinkedinService, self).__init__(*args, **kwargs)

    def _get_linkedin_url(self, person):
        return person.values()[0].get("linkedin_urls")

    def process(self):
        self.logger.info('Starting Process: %s', 'Linkedin Service')
        for person in self.data:
            linkedin_url = self._get_linkedin_url(person)
            if linkedin_url:
                try:
                    data = self._get_profile_by_any_url(linkedin_url)
                    o = {"linkedin_data": data}
                    o.update(person)
                    self.output.append(o)
                except Exception, e:
                    self.logger.error("Linkedin Error: {}".format(e))
        self.logger.info('Ending Process: %s', 'Linkedin Service')
        return self.output

