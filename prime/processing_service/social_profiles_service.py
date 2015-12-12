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

    def _get_extra_pipl_data(self, person):
        linkedin_id = person.get("linkedin_data",{}).get("linkedin_id")
        if linkedin_id:
            request = PiplRequest(linkedin_id, type="linkedin", level="email")
            pipl_data = request.process()        
        else:
            pipl_data = {}        
        return pipl_data

    def process(self):
        for person in self.data:
            pipl_data = self._get_extra_pipl_data(person)
            emails = set(pipl_data.get("emails",[]) + person.get("email_addresses",[]))
            social_accounts = set(pipl_data.get("social_accounts",[]) + person.get("social_accounts",[]))
            images = set(pipl_data.get("images",[]) + person.get("images",[]))
            genders = []
            for email in emails:
                request = PiplRequest(email, type="email", level="social")
                pipl_data = request.process()         
                social_accounts.update(pipl_data.get("social_accounts",[]))           
                images.update(pipl_data.get("images",[]))    
                request = ClearbitRequest(email)
                clearbit_data = request.get_person()       
                social_accounts.update(clearbit_data.get("social_accounts",[]))           
                images.update(clearbit_data.get("images",[]))     
                if clearbit_data.get("gender"):
                    genders.append(clearbit_data.get("gender"))                                
            person["email_addresses"] = list(emails)   
            person["social_accounts"] = list(social_accounts)
            person["images"] = list(images)
            person["clearbit_genders"] = genders
            self.output.append(person)
        return self.output
