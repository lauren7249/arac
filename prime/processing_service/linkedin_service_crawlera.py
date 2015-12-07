import hashlib
import logging
import time
import sys
import os
import boto
from boto.s3.key import Key
import json
import requests
from service import Service, S3SavedRequest

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
                    request = LinkedinRequest(linkedin_url)
                    data = request.process()
                    o = {"linkedin_data": data}
                    o.update(person)
                    self.output.append(o)
                except Exception, e:
                    self.logger.error("Linkedin Error: {}".format(e))
        self.logger.info('Ending Process: %s', 'Linkedin Service')
        return self.output


class LinkedinRequest():

    """
    Given a url, this will return the profile json
    """

    def __init__(self, url):
        self.url = url
        print url
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _validate_data(self, data):
        data = json.loads(data)
        if data.get("linkedin_id") and data.get("full_name"):
            return True
        return False

    def _linkedin_request(self):
        request_data = '{"url":"%s","api_version":"1.0.0"}' % (self.url)
        self.logger.info("Linkedin Request {}".format(request_data))
        result = requests.post("http://10.143.114.140:8888/get_person_by_url",data=request_data)
        if result.status_code == 200 and self._validate_data(result.content):
            return result.content
        time.sleep(1)
        self.logger.warn('Linkedin Failure')
        return None

    def _make_request(self):
        html = self._linkedin_request()
        return html

    def process(self):
        self.logger.info('Linkedin Request: %s', 'Starting')
        html = self._make_request()
        try:
            info = json.loads(html)
            return info
        except:
            return {}
