import logging
import hashlib
import boto
import lxml.html
import re
import dateutil
import requests
from requests import HTTPError
from boto.s3.key import Key

from service import Service, S3SavedRequest
from constants import GLOBAL_HEADERS
from pipl_request import PiplRequest
from clearbit_service import ClearbitRequest

class SocialProfilesService(Service):
    """
    Expected input is JSON with good leads
    Output is going to be existig data enriched with more email accounts and social accounts, as well as other saucy details
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(SocialProfilesService, self).__init__(*args, **kwargs)
                   
    def process(self):
        for person in self.data:
            request = SocialProfilesRequest(person)
            person = request.process()
            self.output.append(person)
        return self.output

class SocialProfilesRequest(S3SavedRequest):

    """
    Given a lead, this will find social profiles and images by any means necessary!
    """

    def __init__(self, person):
        self.person = person
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(SocialProfilesRequest, self).__init__()

    def _get_extra_pipl_data(self):
        linkedin_id = self.person.get("linkedin_data",{}).get("linkedin_id")
        if linkedin_id:
            request = PiplRequest(linkedin_id, type="linkedin", level="email")
            pipl_data = request.process()        
        else:
            pipl_data = {}        
        return pipl_data

    def _update_profile(self, email):
        if not email:
            return
        request = PiplRequest(email, type="email", level="social")
        pipl_data = request.process()         
        self.social_accounts.update(pipl_data.get("social_accounts",[]))           
        self.images.update(pipl_data.get("images",[]))    
        request = ClearbitRequest(email)
        clearbit_data = request.get_person()       
        self.social_accounts.update(clearbit_data.get("social_accounts",[]))           
        self.images.update(clearbit_data.get("images",[]))     
        if clearbit_data.get("gender"):
            self.genders.append(clearbit_data.get("gender"))      

    def _validate_social_accounts(self, social_accounts):
        good_links = []
        for url in social_accounts:
            req = UrlValidatorRequest(url, is_image=False)
            _link = req.process()        
            if _link:
                good_links.append(_link)
        return good_links

    def _validate_images(self, images):
        good_links = []
        for url in images:
            req = UrlValidatorRequest(url, is_image=True)
            _link = req.process()        
            if _link:
                good_links.append(_link)
        return good_links

    def process(self):
        pipl_data = self._get_extra_pipl_data()
        self.emails = set(pipl_data.get("emails",[]) + self.person.get("email_addresses",[]))
        self.social_accounts = set(pipl_data.get("social_accounts",[]) + self.person.get("social_accounts",[]))
        self.images = set(pipl_data.get("images",[]) + self.person.get("images",[]))
        self.genders = []
        for email in self.emails:
            self._update_profile(email)                           
        self.person["email_addresses"] = list(self.emails)   
        self.person["social_accounts"] = self._validate_social_accounts(self.social_accounts)
        self.person["images"] = self._validate_images(self.images)
        self.person["clearbit_genders"] = self.genders    
        return self.person    

class UrlValidatorRequest(S3SavedRequest):

    """
    Given a url, this will return a boolean as to the validity, saving them to S3 as well
    """

    def __init__(self, url, is_image=False):
        super(UrlValidatorRequest, self).__init__()
        self.url = url.lower()
        self.is_image = is_image
        if not self.is_image:
            self.content_type ='text/html'
            self.bucket = None
        else:
            ext = self.url.split(".")[-1]
            if ext == 'png':
                self.content_type = 'image/png'
            else:
                self.content_type = 'image/jpeg'
            s3conn = boto.connect_s3("AKIAIXDDAEVM2ECFIPTA", "4BqkeSHz5SbcAyM/cyTBCB1SwBrB9DDu0Ug/VZaQ")
            self.bucket= s3conn.get_bucket("public-profile-photos")
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        

    def process(self):
        html = self._make_request(content_type =self.content_type , bucket=self.bucket)
        if len(html) > 0:
            if self.is_image:
                return self.boto_key.generate_url(expires_in=0, query_auth=False)
            else:
                return self.url
        return None
