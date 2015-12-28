import hashlib
import logging
import time
import sys
import os
import boto
from boto.s3.key import Key
import json
import requests
import multiprocessing

from service import Service
from saved_request import S3SavedRequest
from person_request import PersonRequest

def wrapper(person):
    linkedin_url = PersonRequest()._get_linkedin_url(person)
    if linkedin_url:
        data = PersonRequest()._get_profile_by_any_url(linkedin_url)
        return data
    return {}

class LinkedinService(Service):
    '''
    Gets linkedin data and collapses by linkedin_id, merging the email addresses, images, and social acounts for the person, 
    as well as the cloudsponge sources from whence the person was obtained
    '''
    def __init__(self, client_data, data, *args, **kwargs):
        super(LinkedinService, self).__init__(*args, **kwargs)
        self.client_data = client_data
        self.data = data
        self.output = {}
        self.wrapper = wrapper
        self.intermediate_output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _get_linkedin_url(self, person):
        return person.values()[0].get("linkedin_urls")

    def multiprocess(self):
        return self.process()

    def _collapse(self):
        for i in xrange(0, len(self.data)):
            person = self.data[i]
            data = self.intermediate_output[i]
            email = person.keys()[0]
            email_data = person.values()[0]                
            linkedin_id = data.get("linkedin_id")
            info = self.output.get(linkedin_id,{})
            emails = info.get("email_addresses",[]) 
            emails.append(email)                 
            social_accounts = info.get("social_accounts",[]) + email_data.get("social_accounts",[])
            sources = info.get("sources",[]) + email_data.get("sources",[])
            images = info.get("images",[]) + email_data.get("images",[])
            o = {"linkedin_data": data, "email_addresses":list(set(emails)), "sources":list(set(sources)), 
                "social_accounts":list(set(social_accounts)), "images":list(set(images))}
            job_title = email_data.get("job_title") 
            companies = email_data.get("companies")
            if companies and len(companies) and companies[0] is not None:
                company = companies[0]
            else:
                company = None   
            if job_title:
                o["job_title"] = job_title
                o["company"] = company                        
            info.update(o)
            self.output.update({linkedin_id:o})    
        return self.output

    def multiprocess(self):
        self.logger.info('Starting MultiProcess: %s', 'Linkedin Service')
        self.pool = multiprocessing.Pool(self.pool_size)
        self.intermediate_output = self.pool.map(self.wrapper, self.data)
        self.pool.close()
        self.pool.join()
        self.output = self._collapse() 
        self.logger.info('Ending MultiProcess: %s', 'Linkedin Service')
        return self.output.values()

    def process(self):
        self.logger.info('Starting Process: %s', 'Linkedin Service')
        for person in self.data:
            person = self.wrapper(person)
            self.intermediate_output.append(person)
        self.output = self._collapse() 
        self.logger.info('Ending Process: %s', 'Linkedin Service')
        return self.output.values()

