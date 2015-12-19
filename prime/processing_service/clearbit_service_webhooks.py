import clearbit
import logging
import hashlib
import boto
import multiprocessing
import re
import json
import time
from requests import HTTPError
from boto.s3.key import Key
from helper import get_domain
from service import Service, S3SavedRequest
from prime.processing_service.constants import pub_profile_re, CLEARBIT_KEY
from clearbit_request_webhooks import ClearbitRequest

def unwrap_process_person(person):
    email = person.keys()[0]
    request = ClearbitRequest(email)
    data = request.get_person()
    return data

class ClearbitPersonService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts and Linkedin IDs via PIPL
    rate limit is 600/minute
    """

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ClearbitPersonService, self).__init__(*args, **kwargs)

    def _merge(self, original_data, output_data):
        for i in xrange(0, len(original_data)):
            original_person = original_data[i].values()[0]
            output_person = output_data[i].values()[0]
            social_accounts = original_person.get("social_accounts",[]) + output_person.get("social_accounts",[])
            sources = original_person.get("sources",[]) + output_person.get("sources",[])
            images = original_person.get("images",[]) + output_person.get("images",[])
            linkedin_urls = original_person.get("linkedin_urls") if original_person.get("linkedin_urls") else output_person.get("linkedin_urls")
            output_data[i][output_data[i].keys()[0]]["social_accounts"] = social_accounts
            output_data[i][output_data[i].keys()[0]]["linkedin_urls"] = linkedin_urls
            output_data[i][output_data[i].keys()[0]]["images"] = images
            output_data[i][output_data[i].keys()[0]]["sources"] = sources
        return output_data

    def multiprocess(self, poolsize=5, merge=True):
        #rate limit is 600/minute
        self.logger.info('Starting MultiProcess: %s', 'Clearbit Service')
        pool = multiprocessing.Pool(processes=poolsize)
        self.output = pool.map(unwrap_process_person, self.data)
        pool.close()
        pool.join()
        if merge:
            self.output = self._merge(self.data,self.output)
        self.logger.info('Ending MultiProcess: %s', 'Clearbit Service')
        return self.output

    def _exclude_person(self, person):
        if len(person.values()) > 0 and person.values()[0].get("linkedin_urls"):
            return True
        return False

    def process(self, merge=True):
        self.logger.info('Starting Process: %s', 'Clearbit Person Service')
        for person in self.data:
            if self._exclude_person(person) and not merge:
                self.output.append(person)
            else:
                email = person.keys()[0]
                request = ClearbitRequest(email)
                data = request.get_person()
                self.output.append({email: data})
        if merge:
            self.output = self._merge(self.data,self.output)
        self.logger.info('Ending Process: %s', 'Clearbit Person Service')
        return self.output

class ClearbitPhoneService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be company info from clearbit
    rate limit is 600/minute with webhooks
    TODO: change to webhooks (instead of streaming)
    """

    def __init__(self, client_data, data, *args, **kwargs):
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ClearbitPhoneService, self).__init__(*args, **kwargs)

    def process(self, overwrite=False):
        self.logger.info('Starting Process: %s', 'Clearbit Phone Service')
        for person in self.data:
            if (not overwrite and person.get("phone_number")) or (not person.get("company_website")):
                self.logger.info('Skipping clearbit phone service. Phone: %s, website: %s', person.get("phone_number",""), person.get("company_website",""))
                self.output.append(person)
            else:
                website = person.get("company_website")
                request = ClearbitRequest(get_domain(website))
                company = request.get_company()
                if company.get("phone_number"):
                    person.update({"phone_number": company.get("phone_number")})
                self.output.append(person)
        self.logger.info('Ending Process: %s', 'Clearbit Phone Service')
        return self.output



