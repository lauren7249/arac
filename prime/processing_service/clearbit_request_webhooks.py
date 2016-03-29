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

    def __init__(self, query):
        super(ClearbitRequest, self).__init__()
        self.clearbit = clearbit
        self.clearbit.key=CLEARBIT_KEY
        self.query = query
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _get_entity(self, type):
        self.logger.info('Make Request: %s', 'Query Clearbit')
        try:
            if type=="person":
                entity = clearbit.Person.find(email=self.query, stream=False, webhook_id=self.query)
            elif type=="company":
                entity = clearbit.Company.find(domain=self.query, stream=False, webhook_id=self.query)
            else:
                entity = None
        except HTTPError as e:
            self.logger.info('Clearbit Fail')
            return None
        return entity

    def _make_request(self, type):
        entity = {}
        if not self.query:
            return entity
        self.key = hashlib.md5("clearbit{}{}".format(type,self.query)).hexdigest()
        key = Key(self.bucket)
        key.key = self.key
        if key.exists():
            self.logger.info('Make Request: %s', 'Get From S3')
            html = key.get_contents_as_string()
            entity = json.loads(html.decode("utf-8-sig"))
        else:
            while True:
                entity = self._get_entity(type)
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
            key.set_contents_from_string(unicode(json.dumps(entity, ensure_ascii=False)))
        entity.pop("id",None)
        entity.pop("fuzzy",None)
        return entity


    def _social_accounts(self):
        social_accounts = []
        if not self.clearbit_json:
            return social_accounts
        for key in self.clearbit_json.keys():
            if isinstance(self.clearbit_json[key], dict) and self.clearbit_json[key].get('handle'):
                handle = self.clearbit_json[key].pop("handle")
                if key=='angellist':
                    link = "https://angel.co/{}".format(handle)
                elif key=='foursquare':
                    link = "https://{}.com/user/{}".format(key, handle)
                elif key=='googleplus':
                    link = "https://plus.google.com/{}".format(handle)
                elif key=='twitter':
                    link = "https://twitter.com/{}".format(handle)
                elif key=='facebook':
                    if handle.isdigit():
                        link = "https://facebook.com/people/_/{}".format(handle)
                    else:
                        link = "https://facebook.com/{}".format(handle)
                elif key=='linkedin':
                    link = "https://www.{}.com/{}".format(key, handle)
                else:
                    link = "https://{}.com/{}".format(key, handle)
                social_accounts.append(link)
        return social_accounts

    def _images(self):
        images = []
        if not self.clearbit_json:
            return images
        for key in self.clearbit_json.keys():
            if isinstance(self.clearbit_json[key], dict) and self.clearbit_json[key].get('avatar'):
                avatar = self.clearbit_json[key].pop("avatar")
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
        self.clearbit_json = self._make_request("person")
        social_accounts = self._social_accounts()
        linkedin_url = self._linkedin_url(social_accounts)
        images = self._images()
        data = {"social_accounts": social_accounts,
                "linkedin_url": linkedin_url,
                "images": images,
                "clearbit_fields": self.clearbit_json}
        if self.clearbit_json and self.clearbit_json.get("gender"):
            data["gender"] = self.clearbit_json.pop("gender")
        return data

    def get_company(self):
        self.logger.info('Clearbit Company Request: %s', 'Starting')
        response = {}
        self.clearbit_json = self._make_request("company")
        return {"phone_number": self.clearbit_json.get('phone'), 
                "geo": self.clearbit_json.get('geo'), 
                "clearbit_fields":self.clearbit_json
                }
