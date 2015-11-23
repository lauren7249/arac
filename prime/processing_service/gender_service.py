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
from helper import get_firstname
from gender_detector import GenderDetector
from genderizer.genderizer import Genderizer
import sexmachine.detector as gender

class GenderService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existig data enriched with genders
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        self.detector1 = GenderDetector('us')
        self.detector2 = gender.Detector()
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(GenderService, self).__init__(*args, **kwargs)

    def process(self, favor_mapquest=False, favor_clearbit=False):
        for person in self.data:
            firstname = get_firstname(person.get("linkedin_data").get("full_name"))
            is_male = self._get_gender(firstname)
            if is_male is None:
                person["gender"] = "Unknown"
            elif is_male:
                person["gender"] = "Male"
            else:
                person["gender"] = "Female"
            self.output.append(person)
        return self.output

    def _get_gender_from_free_apis(self,str):
        gender_str = self.detector2.get_gender(str)
        if "andy" in gender_str: gender_str = self.detector1.guess(str)
        if "unknown" in gender_str: gender_str = Genderizer.detect(firstName = str)
        if gender_str is None: return None
        if "female" in gender_str: return False
        if "male" in gender_str: return True
        return None

    def _get_gender_from_search(self,str):
        url = "http://search.yahoo.com/search?q=facebook.com:%20" + str
        headers ={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        response = requests.get(url, headers=GLOBAL_HEADERS)
        response_text = response.text.lower()
        male_indicators = response_text.count(" he ") + response_text.count(" his ")
        female_indicators = response_text.count(" she ") + response_text.count(" her ")
        if female_indicators>male_indicators: return False
        if male_indicators>female_indicators: return True
        return None

    def _get_gender(self,str):
        gender = self._get_gender_from_free_apis(str)
        if gender is None: gender = self._get_gender_from_search(str)
        return gender
