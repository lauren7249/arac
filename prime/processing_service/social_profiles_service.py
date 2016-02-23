import logging
import hashlib
import boto
import lxml.html
import re
import json
import dateutil
import requests
from requests import HTTPError
from boto.s3.key import Key

from service import Service, S3SavedRequest
from constants import GLOBAL_HEADERS, ALCHEMY_API_KEYS, SOCIAL_DOMAINS
from pipl_request import PiplRequest
from clearbit_service_webhooks import ClearbitRequest
from url_validator import UrlValidatorRequest
from prime.utils.alchemyapi import AlchemyAPI
from random import shuffle
import timeout_decorator

def wrapper(person):
    try:
        request = SocialProfilesRequest(person)
        person = request.process()    
        return person
    except Exception, e:
        print __name__ + str(e)
        return person
        
class SocialProfilesService(Service):
    """
    Expected input is JSON with good leads
    Output is going to be existig data enriched with more email accounts and social accounts, as well as other saucy details
    """

    def __init__(self, data, *args, **kwargs):
        super(SocialProfilesService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper
        self.pool_size = 20
        
                   
class SocialProfilesRequest(S3SavedRequest):

    """
    Given a lead, this will find social profiles and images by any means necessary! It will also tag them =)
    """

    def __init__(self, person):
        super(SocialProfilesRequest, self).__init__()
        self.person = person
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        shuffle(ALCHEMY_API_KEYS)
        self.api_key = ALCHEMY_API_KEYS[0]
        self.alchemyapi = AlchemyAPI(self.api_key)

    #@timeout_decorator.timeout(5)
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

    def _process_social_accounts(self, social_accounts):
        good_links = []
        for url in social_accounts:
            domain = url.replace("https://","").replace("http://","").split("/")[0].replace("www.","").split(".")[0].lower()
            if domain not in SOCIAL_DOMAINS or domain is None: 
                continue            
            req = UrlValidatorRequest(url, is_image=False)
            _link = req.process()        
            if _link:
                good_links.append(_link)
                #self.logger.info(_link + " was AWESOME")
            else:
                self.logger.warn("{} was invalid".format(_link))
        return good_links

    def _get_alchemy_tags(self, url):
        if not url:
            return {}
        query = "alchemyapiimageTaggingurl" + url
        key = hashlib.md5(query).hexdigest()
        bucket = self.bucket
        boto_key = Key(bucket)
        boto_key.key = key        
        if boto_key.exists():
            html = boto_key.get_contents_as_string()
            try:
                return json.loads(html.decode("utf-8-sig"))
            except:
                return {}
        else:
            response = self.alchemyapi.imageTagging('url', url)
            if response and response.get("imageKeywords"):
                output = response.get("imageKeywords")
            else:
                output = {}
            boto_key.set_contents_from_string(unicode(json.dumps(output, ensure_ascii=False)))
            return output
        return {}

    def _get_image_tags(self, url):
        _tags = self._get_alchemy_tags(url)
        tags = {}
        for tag in _tags:
            try:
                score = float(tag.get("score"))
                if score<=0.5: 
                    continue
            except:
                continue
            tags.update({tag.get("text"):score})
        #this is the blank profile pic option
        if len(tags)==1 and tags.keys()[0] in ["instagram","moon"]:
            return {}
        return tags

    def _process_images(self, images):
        good_links = {}
        for url in images:
            if not url:
                continue
            req = UrlValidatorRequest(url, is_image=True)
            _link = req.process()        
            if _link:
                tags = self._get_image_tags(_link)
                if len(tags):
                    good_links.update({_link:tags})
        return good_links

    def process(self):
        pipl_data = self._get_extra_pipl_data()
        self.emails = set(pipl_data.get("emails",[]) + self.person.get("email_addresses",[]))
        self.social_accounts = set(pipl_data.get("social_accounts",[]) + self.person.get("social_accounts",[]))
        self.images = set(pipl_data.get("images",[]) + self.person.get("images",[]) + [self.person.get("linkedin_data",{}).get("image")])
        self.phone_numbers = pipl_data.get("phones",[])
        self.addresses = pipl_data.get("addresses",[])
        self.genders = []
        for email in self.emails:
            self._update_profile(email)                           
        self.person["email_addresses"] = list(self.emails)   
        self.person["social_accounts"] = self._process_social_accounts(self.social_accounts)
        self.person["images_with_tags"] = self._process_images(self.images)
        self.person["clearbit_genders"] = self.genders    
        self.person["pipl_phone_numbers"] = self.phone_numbers
        self.person["pipl_addresses"] = self.addresses
        return self.person    

