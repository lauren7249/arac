import clearbit
import logging
import hashlib
import boto
import multiprocessing
import re
from requests import HTTPError
from boto.s3.key import Key
from helper import get_domain
from service import Service, S3SavedRequest
from prime.processing_service.constants import pub_profile_re

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

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ClearbitPersonService, self).__init__(*args, **kwargs)

    def dispatch(self):
        pass

    def _merge(self, original_data, output_data):
        for i in xrange(0, len(original_data)):
            original_person = original_data[i].values()[0]
            output_person = output_data[i].values()[0]
            social_accounts = original_person.get("social_accounts",[]) + output_person.get("social_accounts",[])
            linkedin_urls = original_person.get("linkedin_urls") if original_person.get("linkedin_urls") and re.search(pub_profile_re,original_person.get("linkedin_urls")) else output_person.get("linkedin_urls")
            output_data[i][output_data[i].keys()[0]]["social_accounts"] = social_accounts
            output_data[i][output_data[i].keys()[0]]["linkedin_urls"] = linkedin_urls
        return output_data

    def multiprocess(self, poolsize=5, merge=False):
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

    def process(self, merge=False):
        self.logger.info('Starting Process: %s', 'Clearbit Person Service')
        for person in self.data:
            if self._exclude_person(person) and not merge:
                self.output.append(person)
            else:
                email = person.keys()[0]
                request = ClearbitRequest(email)
                data = request.get_person()
                self.output.append(data)
        if merge:
            self.output = self._merge(self.data,self.output)
        self.logger.info('Ending Process: %s', 'Clearbit Person Service')
        return self.output

class ClearbitPhoneService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be company info from clearbit
    rate limit is 600/minute
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ClearbitPhoneService, self).__init__(*args, **kwargs)

    def process(self, overwrite=False):
        self.logger.info('Starting Process: %s', 'Clearbit Company Service')
        for person in self.data:
            if (not overwrite and person.get("phone_number")) or not person.get("company_website"):
                self.output.append(person)
            else:
                website = person.get("company_website")
                request = ClearbitRequest(get_domain(website))
                company = request.get_company()
                person.update({"phone_number": company.get("phone_number")})
                self.output.append(person)
        self.logger.info('Ending Process: %s', 'Clearbit Company Service')
        return self.output

class ClearbitRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via Clearbit
    """

    def __init__(self, query, type='email'):
        self.clearbit = clearbit
        self.clearbit.key='f2512e10a605e3dcaff606205dbd3758'
        self.query = query
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ClearbitRequest, self).__init__()

    def _make_request(self, type):
        self.key = hashlib.md5(self.query).hexdigest()
        key = Key(self._s3_connection)
        key.key = self.key
        if key.exists():
            self.logger.info('Make Request: %s', 'Get From S3')
            html = key.get_contents_as_string()
        else:
            try:
                self.logger.info('Make Request: %s', 'Query Clearbit')
                if type=="person":
                    entity = clearbit.Person.find(email=self.query, stream=True)
                elif type=="company":
                    entity = clearbit.Company.find(domain=self.query, stream=True)
            except HTTPError as e:
                self.logger.info('Clearbit Fail')
                entity = None
            if entity:
                #TODO, this doesn't work
                try:
                    key.content_type = 'text/html'
                    key.set_contents_from_string(entity)
                except:
                    pass
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
                    link = "https://facebook.com/" + handle
                elif key=='linkedin':
                    link = "https://www." + key + ".com/" + handle
                else:
                    link = "https://" + key + ".com/" + handle
                social_accounts.append(link)
        return social_accounts

    def _linkedin_url(self, social_accounts):
        for record in social_accounts:
            if "linkedin.com" in record:
                return record
        self.logger.warn('Linkedin: %s', 'Not Found')
        return None

    def get_person(self):
        self.logger.info('Clearbit Person Request: %s', 'Starting')
        response = {}
        clearbit_json = self._make_request("person")
        social_accounts = self._social_accounts(clearbit_json)
        linkedin_url = self._linkedin_url(social_accounts)
        data = {"social_accounts": social_accounts,
                "linkedin_urls": linkedin_url,
                "clearbit_fields": clearbit_json}
        response[self.query] = data
        return response

    def get_company(self):
        self.logger.info('Clearbit Company Request: %s', 'Starting')
        response = {}
        clearbit_json = self._make_request("company")
        return {"phone_number": clearbit_json['phone'], "clearbit_fields":clearbit_json}



