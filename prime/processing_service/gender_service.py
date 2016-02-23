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
GENDER_DETECTOR_1 = GenderDetector('us')
GENDER_DETECTOR_2 = gender.Detector()

logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wrapper(person):
    try:
        genders = person.get("clearbit_genders",[])
        malecount= genders.count("male") 
        femalecount = genders.count("female")
        firstname = get_firstname(person.get("linkedin_data",{}).get("full_name"))
        if malecount and not femalecount:
            person["gender"] = "male"
        elif femalecount and not malecount:
            person["gender"] = "female"
        else:
            is_male = GenderRequest(firstname).process()
            if is_male is None:
                person["gender"] = "unknown"
            elif is_male:
                person["gender"] = "male"
            else:
                person["gender"] = "female"  
        logger.info("{} is {}".format(firstname, person.get("gender")))
        return person
    except Exception, e:
        print __name__ + str(e)
        return person
     
class GenderService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existig data enriched with genders
    """

    def __init__(self, data, *args, **kwargs):
        super(GenderService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper

class GenderRequest(S3SavedRequest):

    """
    Given a first name, this will get a gender boolean (true=Male, false=Female, None=unknown)
    """
    def __init__(self, name):
        super(GenderRequest, self).__init__()
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.name = name
        self.logger = logging.getLogger(__name__)        
        self.detector1 = GENDER_DETECTOR_1
        self.detector2 = GENDER_DETECTOR_2
                
    def _get_gender_from_free_apis(self):
        if not self.name:
            return None
        try:
            gender_str = self.detector2.get_gender(self.name)
        except:
            gender_str = "andy"
        if "andy" in gender_str: 
            try:
                gender_str = self.detector1.guess(self.name)
            except:
                gender_str = "unknown" 
        if "unknown" in gender_str: 
            try:
                gender_str = Genderizer.detect(firstName = self.name)
            except:
                gender_str = None
        if gender_str is None: return None
        if "female" in gender_str: return False
        if "male" in gender_str: return True
        return None

    def _get_gender_from_search(self):
        if not self.name:
            return None
        self.url = "http://search.yahoo.com/search?q=facebook.com:%20" + self.name
        response_text = self._make_request().lower()
        male_indicators = response_text.count(" he ") + response_text.count(" his ")
        female_indicators = response_text.count(" she ") + response_text.count(" her ")
        if female_indicators>male_indicators: return False
        if male_indicators>female_indicators: return True
        return None

    def process(self):
        if not self.name:
            return None
        gender = self._get_gender_from_free_apis()
        if gender is None: gender = self._get_gender_from_search()
        return gender
