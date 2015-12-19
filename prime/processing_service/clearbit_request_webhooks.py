import clearbit
import logging
import hashlib
import boto
import re
import json
import time
from requests import HTTPError
from boto.s3.key import Key
from service import S3SavedRequest
from prime.processing_service.constants import CLEARBIT_KEY

class ClearbitRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via Clearbit
    """

    def __init__(self, query, type='person'):
        super(ClearbitRequest, self).__init__()
        self.clearbit = clearbit
        self.clearbit.key=CLEARBIT_KEY
        self.query = query
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _get_entity(self, query, type):
        self.logger.info('Make Request: %s', 'Query Clearbit')
        try:
            if type=="person":
                entity = clearbit.Person.find(email=query, stream=False, webhook_id=self.query)
            elif type=="company":
                entity = clearbit.Company.find(domain=query, stream=False, webhook_id=self.query)
            else:
                entity = None
        except HTTPError as e:
            self.logger.info('Clearbit Fail')        
            return None
        return entity

    def _make_request(self, type):
        entity = {}
        self.key = hashlib.md5("clearbit" + type + self.query).hexdigest()
        key = Key(self.bucket)
        key.key = self.key
        if key.exists() and False:
            self.logger.info('Make Request: %s', 'Get From S3')
            html = key.get_contents_as_string()
            entity = json.loads(html)
        else:
            while True:
                entity = self._get_entity(self.query, type)
                if not entity:
                    entity = {}
                    break     
                entity = dict(entity)           
                if entity.get("pending",False):
                    self.logger.info('Clearbit Response PENDING')
                    time.sleep(2)                
                else:
                    break
            entity.pop('response', None)
            key.content_type = 'text/html'
            key.set_contents_from_string(json.dumps(entity))
        return entity


    def _social_accounts(self, clearbit_json):
        social_accounts = []
        if not clearbit_json:
            return social_accounts
        for key in clearbit_json.keys():
            if isinstance(clearbit_json[key], dict) and clearbit_json[key].get('handle'):
                handle = clearbit_json[key].get("handle")
                if key=='angellist':
                    link = "https://angel.co/" + handle
                elif key=='foursquare':
                    link = "https://" + key + ".com/user/" + handle
                elif key=='googleplus':
                    link = "https://plus.google.com/" + handle
                elif key=='twitter':
                    link = "https://twitter.com/" + handle
                elif key=='facebook':
                    if handle.isdigit():
                        link = "https://facebook.com/people/_/" + handle
                    else:
                        link = "https://facebook.com/" + handle
                elif key=='linkedin':
                    link = "https://www." + key + ".com/" + handle
                else:
                    link = "https://" + key + ".com/" + handle
                social_accounts.append(link)
        return social_accounts

    def _images(self, clearbit_json):
        images = []
        if not clearbit_json:
            return images
        for key in clearbit_json.keys():
            if isinstance(clearbit_json[key], dict) and clearbit_json[key].get('avatar'):
                avatar = clearbit_json[key].get("avatar")
                images.append(avatar)
        return images

    def _linkedin_url(self, social_accounts):
        for record in social_accounts:
            if "linkedin.com" in record:
                return record
        self.logger.warn('Linkedin: %s', 'Not Found')
        return None

    def get_person(self):
        self.logger.info('Clearbit Person Request: %s', 'Starting')
        clearbit_json = self._make_request("person")
        social_accounts = self._social_accounts(clearbit_json)
        linkedin_url = self._linkedin_url(social_accounts)
        images = self._images(clearbit_json)
        data = {"social_accounts": social_accounts,
                "linkedin_urls": linkedin_url,
                "images": images,
                "clearbit_fields": clearbit_json}
        if clearbit_json and clearbit_json.get("gender"):
            data["gender"] = clearbit_json.get("gender")
        return data

    def get_company(self):
        self.logger.info('Clearbit Company Request: %s', 'Starting')
        response = {}
        clearbit_json = self._make_request("company")
        return {"phone_number": clearbit_json.get('phone'), "clearbit_fields":clearbit_json}
