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
from helper import parse_date

def wrapper(person):
    try:
        college_grad = CollegeDegreeRequest()._has_college_degree(person.get("linkedin_data",{}))
        person["college_grad"] = college_grad    
        return person
    except Exception, e:
        print __name__ + str(e)
        return person
        
class CollegeDegreeService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existig data enriched with college_grad boolean
    """

    def __init__(self, data, *args, **kwargs):
        super(CollegeDegreeService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper

class CollegeDegreeRequest(S3SavedRequest):

    def __init__(self):
        super(CollegeDegreeRequest, self).__init__()
        self.logger = logging.getLogger(__name__)

    def _has_college_degree(self, person):
        for school in person.get("schools",[]):
            #it's a high school so lets move on
            if school.get("college") and school.get("college","").lower().find("high school") > -1:
                continue
            #still in school; hasnt earned degree
            if school.get("end_date") == "Present":
                continue
            #definitely a college degree if it's a bachelors
            if school.get("degree_type"):
                degree = school.get("degree_type")
            elif school.get("degree"):
                degree = school.get("degree")
            else:
                degree = None
            if degree is not None:
                clean_degree = re.sub('[^0-9a-z\s]','',degree.lower().strip())
                if re.search('^bs($|\s)', clean_degree) or re.search('^ba($|\s)', clean_degree) or re.search('^ab($|\s)', clean_degree) or re.search('^bachelor[s]*($|\s)', clean_degree):
                    return True
            #looks like a college or university. you need to be a college of some kind to have a college ID. proof: philips exeter academy does not have one. they only have a company page
            college = school.get("college") if school.get("college") else ""
            if school.get("college_id") or college.lower().find('university')>-1 or college.lower().find('college')>-1:
                start_date = parse_date(school.get("start_date"))
                end_date = parse_date(school.get("end_date"))
                #cant be a 4-year degree if you finished in less than 3 years
                if end_date and start_date and end_date.year - start_date.year < 3:
                    continue
                return True
        return False
