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
    '''
    Gets linkedin data and collapses by linkedin_id
    '''
    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = {}
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(LinkedinService, self).__init__(*args, **kwargs)

    def _get_linkedin_url(self, person):
        return person.values()[0].get("linkedin_urls")

    def process(self):
        self.logger.info('Starting Process: %s', 'Linkedin Service')
        for person in self.data:
            email = person.keys()[0]
            email_data = person.values()[0]
            linkedin_url = self._get_linkedin_url(person)
            if linkedin_url:
                data = self._get_profile_by_any_url(linkedin_url)
                if data:
                    linkedin_id = data.get("linkedin_id")
                    info = self.output.get(linkedin_id,{})
                    emails = info.get("email_addresses",[]) 
                    emails.append(email)
                    social_accounts = info.get("social_accounts",[]) + email_data.get("social_accounts",[])
                    images = info.get("images",[]) + email_data.get("images",[])
                    o = {"linkedin_data": data, "email_addresses":list(set(emails)), "social_accounts":list(set(social_accounts)), "images":list(set(images))}
                    info.update(o)
                    self.output.update({linkedin_id:o})
        self.logger.info('Ending Process: %s', 'Linkedin Service')
        return self.output.values()

