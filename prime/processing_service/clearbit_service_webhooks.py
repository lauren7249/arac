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
from helpers.stringhelpers import domestic_area

def person_wrapper(person):
    email = person.keys()[0]
    data = person.values()[0]
    # if data.get("linkedin_urls"):
    #     return {email:data}   
    try:
        request = ClearbitRequest(email)
        data = request.get_person()
        return {email:data}   
    except Exception, e:
        print __name__ + str(e)
        return {email:{}}

class ClearbitPersonService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts and Linkedin IDs via clearbit
    rate limit is 600/minute
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(ClearbitPersonService, self).__init__(*args, **kwargs)
        self.client_data = client_data
        self.data = data
        self.output = []
        self.wrapper = person_wrapper
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def _merge(self, original_data, output_data):
        _linkedin_urls_found  = 0
        for i in xrange(0, len(original_data)):
            original_person = original_data[i].values()[0]
            output_person = output_data[i].values()[0]
            social_accounts = original_person.get("social_accounts",[]) + output_person.get("social_accounts",[])
            sources = original_person.get("sources",[]) + output_person.get("sources",[])
            images = original_person.get("images",[]) + output_person.get("images",[])
            linkedin_urls = original_person.get("linkedin_urls") if original_person.get("linkedin_urls") else output_person.get("linkedin_urls")
            if linkedin_urls:
                _linkedin_urls_found+=1
            output_data[i][output_data[i].keys()[0]]["social_accounts"] = social_accounts
            output_data[i][output_data[i].keys()[0]]["linkedin_urls"] = linkedin_urls
            output_data[i][output_data[i].keys()[0]]["images"] = images
            output_data[i][output_data[i].keys()[0]]["sources"] = sources
            #the one that has the job title is the linkedin record
            output_data[i][output_data[i].keys()[0]]["job_title"] = original_person.get("job_title") if original_person.get("job_title") else output_person.get("job_title")
            output_data[i][output_data[i].keys()[0]]["companies"] = original_person.get("companies") if original_person.get("job_title") else output_person.get("companies")
            output_data[i][output_data[i].keys()[0]]["first_name"] = original_person.get("first_name") if original_person.get("job_title") else output_person.get("first_name")
            output_data[i][output_data[i].keys()[0]]["last_name"] = original_person.get("last_name") if original_person.get("job_title") else output_person.get("last_name")      
        self.logger.info("{} linkedin urls found".format(_linkedin_urls_found))      
        return output_data

    def process(self):
        self.logstart()
        try:
            for person in self.data:     
                person = person_wrapper(person)
                self.output.append(person)      
            self.output = self._merge(self.data,self.output)
        except:
            self.logerror()
        self.logend()
        return self.output

    def multiprocess(self):
        self.logstart()
        try:
            self.pool = multiprocessing.Pool(self.pool_size)
            self.output = self.pool.map(self.wrapper, self.data)
            self.pool.close()
            self.pool.join()
            self.output = self._merge(self.data,self.output)
        except:
            self.logerror()
        self.logend()
        return self.output

def phone_wrapper(person, overwrite=False):
    try:
        if (not overwrite and domestic_area(person.get("phone_number"))) or (not person.get("company_website")):
            #logger.info('Skipping clearbit phone service. Phone: %s, website: %s', person.get("phone_number",""), person.get("company_website",""))
            return person
        website = person.get("company_website")
        request = ClearbitRequest(get_domain(website))
        company = request.get_company()
        if domestic_area(company.get("phone_number")):
            person.update({"phone_number": company.get("phone_number")})
        return person
    except Exception, e:
        print __name__ + str(e)
        return person
        
class ClearbitPhoneService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be company info from clearbit
    rate limit is 600/minute with webhooks
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(ClearbitPhoneService, self).__init__(*args, **kwargs)
        self.data = data
        self.output = []
        self.wrapper = phone_wrapper
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)




