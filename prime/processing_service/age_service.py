import logging
import hashlib
import boto
import lxml.html
import re
import dateutil
import numpy
import requests
from requests import HTTPError
from boto.s3.key import Key
import datetime
from service import Service, S3SavedRequest
from constants import GLOBAL_HEADERS
from helpers.linkedin_helpers import get_dob_year_range

def wrapper(person):
    try:
        req = AgeRequest()
        linkedin_data = person.get("linkedin_data")
        dob_range = req._get_dob_year_range(linkedin_data)
        age = req._get_age(linkedin_data)
        person["age"] = age
        if dob_range and len(dob_range)==2:
            person["dob_min"] = dob_range[0]
            person["dob_max"] = dob_range[1]
        return person
    except Exception, e:
        print __name__ + str(e)
        return person
        
class AgeService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existig data enriched with ages
    """

    def __init__(self, data, *args, **kwargs):
        super(AgeService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper

class AgeRequest(S3SavedRequest):

    name = "age_request"
    def __init__(self):
        super(AgeRequest, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.dob_year_range = None

    def _get_age(self, linkedin_data):
        self.linkedin_data = linkedin_data 
        dob_year = self._get_dob_year(self.linkedin_data)
        if not dob_year: return None
        return datetime.datetime.today().year - dob_year

    def _get_dob_year(self, linkedin_data):
        self.linkedin_data = linkedin_data 
        dob_year_range = self._get_dob_year_range(self.linkedin_data)
        if not max(dob_year_range): return None
        return numpy.mean(dob_year_range)

    def _get_dob_year_range(self, linkedin_data):
        self.linkedin_data = linkedin_data        
        if self.dob_year_range:
            return self.dob_year_range
        dob_year_min = None
        dob_year_max = None
        if not self.linkedin_data:
            return (dob_year_min, dob_year_max)        
        educations = self.linkedin_data.get("schools",[])
        experiences = self.linkedin_data.get("experiences",[])
        self.dob_year_range = get_dob_year_range(educations, experiences)
        return self.dob_year_range

