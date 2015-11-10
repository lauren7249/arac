import logging
import hashlib
import boto
import lxml.html
import re
import dateutil
from requests import HTTPError
from boto.s3.key import Key

from service import Service, S3SavedRequest

class BloombergService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be existig data enriched with bloomberg phone numbers
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(BloombergService, self).__init__(*args, **kwargs)

    def dispatch(self):
        pass


    def process(self):
        self.logger.info('Starting Process: %s', 'Clearbit Service')
        for person in self.data:
            current_job = self._current_job(person)
            if current_job:
                request = BloombergRequest(current_job.get("company"))
                data = request.process()
                person.update({"phone_number": data})
            self.output.append(person)
        self.logger.info('Ending Process: %s', 'Clearbit Service')
        return self.output


class BloombergRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via Clearbit
    """

    def __init__(self, query):
        self.query = query
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(BloombergRequest, self).__init__()

    def _make_request(self):
        return None

    def process(self):
        self.logger.info('Bloomberg Request: %s', 'Starting')
        response = {}
        bloomberg_number = self._make_request()
        return bloomberg_number




