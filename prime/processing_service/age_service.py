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
from nameko.rpc import rpc

class AgeService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existig data enriched with ages
    """

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(AgeService, self).__init__(*args, **kwargs)

    def process(self):
        for person in self.data:
            req = AgeRequest()
            linkedin_data = person.get("linkedin_data")
            dob_range = req._get_dob_year_range(linkedin_data)
            age = req._get_age(linkedin_data)
            person["age"] = age
            if dob_range and len(dob_range)==2:
                person["dob_min"] = dob_range[0]
                person["dob_max"] = dob_range[1]
            self.output.append(person)
        return self.output


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
        school_milestones = self._get_school_milestones(self.linkedin_data.get("schools",[]))
        first_school_year = school_milestones.get("first_school_year")
        first_grad_year = school_milestones.get("first_grad_year")
        if first_school_year:
            dob_year_max = first_school_year - 17
            dob_year_min = first_school_year - 20
        elif first_grad_year:
            dob_year_max = first_grad_year - 21
            dob_year_min = first_grad_year - 25
        if dob_year_min: 
            self.dob_year_range = (dob_year_min, dob_year_max)
            return self.dob_year_range
        work_milestones = self._get_work_milestones(self.linkedin_data.get("experiences",[]))
        first_year_experience = work_milestones.get("first_year_experience")
        first_quitting_year = work_milestones.get("first_quitting_year")
        if first_year_experience:
            dob_year_max = first_year_experience - 18
            dob_year_min = first_year_experience - 24
        elif first_quitting_year:
            dob_year_max = first_quitting_year - 19
            dob_year_min = first_quitting_year - 28
        #add age-based fuzz factor for people who only list job years
        if dob_year_min:
            dob_year_min -= (datetime.datetime.today().year - dob_year_min)/10
            self.dob_year_range = (dob_year_min, dob_year_max)
            return self.dob_year_range
        first_weird_school_year = school_milestones.get("first_weird_school_year")
        first_weird_grad_year = school_milestones.get("first_weird_grad_year")
        if first_weird_school_year:
            dob_year_max = first_weird_school_year - 14
            dob_year_min = first_weird_school_year - 22
        elif first_weird_grad_year:
            dob_year_max = first_weird_grad_year - 17
            dob_year_min = first_weird_grad_year - 27
        self.dob_year_range = (dob_year_min, dob_year_max)
        return self.dob_year_range

    def _get_school_milestones(self, schools):
        first_school_year = None
        first_grad_year = None
        first_weird_school_year = None
        first_weird_grad_year = None
        for school in schools:
            try:
                start_date = dateutil.parser.parse(school.get("start_date"))
            except:
                start_date = None
            try:
                end_date = dateutil.parser.parse(school.get("end_date"))
            except:
                end_date = None
            if school.get("college_id") or school.get("college","").lower().find('university')>-1 or school.get("college","").lower().find('college')>-1:
                if start_date and (not first_school_year or start_date.year<first_school_year):
                    first_school_year = start_date.year
                if end_date and (not first_grad_year or end_date.year<first_grad_year):
                        first_grad_year = end_date.year
            else:
                if start_date and (not first_weird_school_year or start_date.year<first_weird_school_year):
                    first_weird_school_year = start_date.year
                if end_date and (not first_weird_grad_year or end_date.year<first_weird_grad_year):
                    first_weird_grad_year = end_date.year
        return {"first_school_year":first_school_year,
                "first_grad_year": first_grad_year,
                "first_weird_school_year":first_weird_school_year,
                "first_weird_grad_year": first_weird_grad_year}

    def _get_work_milestones(self,jobs):
        first_year_experience = None
        first_quitting_year = None
        for job in jobs:
            try:
                start_date = dateutil.parser.parse(job.get("start_date"))
            except:
                start_date = None
            try:
                end_date = dateutil.parser.parse(job.get("end_date"))
            except:
                end_date = None
            if start_date and (not first_year_experience or start_date.year<first_year_experience):
                first_year_experience = start_date.year
            if end_date and (not first_quitting_year or end_date.year<first_quitting_year):
                first_quitting_year = end_date.year
        return {"first_year_experience":first_year_experience, "first_quitting_year":first_quitting_year}
