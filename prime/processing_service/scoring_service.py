import logging
import hashlib
import boto
import lxml.html
import re
import dateutil
import requests
from requests import HTTPError
from boto.s3.key import Key
import scipy.stats as stats
from service import Service, S3SavedRequest
from constants import GLOBAL_HEADERS

class ScoringService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existig data enriched with wealth scores
    """

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ScoringService, self).__init__(*args, **kwargs)

    def compute_stars(self):
        all_scores = [profile.get("lead_score") for profile in self.output]
        for i in range(len(self.output)):
            profile = self.output[i]
            percentile = stats.percentileofscore(all_scores, profile.get("lead_score"))
            if percentile > 66: score = 3
            elif percentile > 33: score = 2
            else: score = 1
            profile["stars"] = score
            self.output[i] = profile
        self.output = sorted(self.output, key=lambda k: k['lead_score'], reverse=True) 
        return self.output

    def process(self):
        for person in self.data:
            person["wealthscore"] = WealthScoreRequest(person).process()
            person["lead_score"] = LeadScoreRequest(person).process()
            self.output.append(person)
        return self.compute_stars()

class WealthScoreRequest(S3SavedRequest):

    """
    Given a person, this will get a wealth score
    """

    def __init__(self, person):
        super(WealthScoreRequest, self).__init__()
        self.indeed_salary = person.get("indeed_salary")
        self.glassdoor_salary = person.get("glassdoor_salary")
        self.max_salary = max(self.indeed_salary, self.glassdoor_salary)
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)        
        
    def process(self):
        if not self.max_salary:
            return None
        self.url = "http://www.shnugi.com/income-percentile-calculator/?min_age=18&max_age=100&income=" + str(self.max_salary)
        html = self._make_request()
        try:
            percentile = re.search('(?<=ranks at: )[0-9]+(?=(\.|\%))',html).group(0)
            return int(re.sub("[^0-9]","",percentile))    
        except:
            return None

class LeadScoreRequest(S3SavedRequest):

    """
    Given a person and agent data, this will calculate a lead score
    """

    def __init__(self, person):
        super(LeadScoreRequest, self).__init__()
        self.indeed_salary = person.get("indeed_salary")
        self.glassdoor_salary = person.get("glassdoor_salary")
        self.max_salary = max(self.indeed_salary, self.glassdoor_salary)
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)        
        
    def process(self):
        return 5
