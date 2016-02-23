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
from helper import get_specific_url
import multiprocessing


def wrapper(person):
    try:
        person["wealthscore"] = WealthScoreRequest(person).process()
        person["lead_score"] = LeadScoreRequest(person).process()    
        return person
    except Exception, e:
        print __name__ + " " + str(e)
        person["lead_score"] = -99
        return person

class ScoringService(Service):
    """
    Expected input is JSON with fully built profiles
    Output is going to be existig data enriched with wealth scores
    """

    def __init__(self, data, *args, **kwargs):
        super(ScoringService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper
        
    def compute_stars(self):
        all_scores = [profile.get("lead_score") for profile in self.output]
        for i in range(len(self.output)):
            profile = self.output[i]
            percentile = stats.percentileofscore(all_scores, profile.get("lead_score"))
            if percentile >=80: score = 5
            elif percentile >= 60: score = 4
            elif percentile >= 40: score = 3
            elif percentile >=20: score = 2
            else: score = 1
            profile["stars"] = score
            self.output[i] = profile
        self.output = sorted(self.output, key=lambda k: k['lead_score'], reverse=True) 
        return self.output

    def multiprocess(self):
        self.logstart()
        try:
            self.pool = multiprocessing.Pool(self.pool_size)
            self.output = self.pool.map(self.wrapper, self.data)
            self.pool.close()
            self.pool.join()
            self.output = self.compute_stars()
        except:
            self.logerror()
        self.logend()
        return {"data":self.output, "client_data":self.client_data}

    def process(self):
        self.logstart()
        try:
            for person in self.data:
                person = self.wrapper(person)
                self.output.append(person)
            self.output = self.compute_stars()
        except:
            self.logerror()
        self.logend()
        return {"data":self.output, "client_data":self.client_data}

class WealthScoreRequest(S3SavedRequest):

    """
    Given a fully built profile, this will get a wealth score
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
        self.url = "http://www.shnugi.com/income-percentile-calculator/?min_age=18&max_age=100&income={}".format(str(self.max_salary))
        html = self._make_request()
        try:
            percentile = re.search('(?<=ranks at: )[0-9]+(?=(\.|\%))',html).group(0)
            return int(re.sub("[^0-9]","",percentile))    
        except Exception, e:
            print __name__ + " " + str(e)
            return None

class LeadScoreRequest(S3SavedRequest):

    """
    Given a fully built profile, this will calculate a lead score
    """

    def __init__(self, person):
        super(LeadScoreRequest, self).__init__()
        self.amazon = person.get("amazon")
        self.indeed_salary = person.get("indeed_salary")
        self.glassdoor_salary = person.get("glassdoor_salary")
        self.salary = max(self.indeed_salary, self.glassdoor_salary)
        if not self.salary:
            self.salary = -1
        self.social_accounts = person.get("social_accounts",[])
        self.common_schools = person.get("common_schools",[])
        self.referrers = person.get("referrers",[])
        self.emails = person.get("email_addresses",[])
        self.sources = person.get("sources",[])
        self.images = person.get("profile_image_urls",{})
        if not self.social_accounts:
            self.social_accounts = []
        if not self.common_schools:
            self.common_schools = []
        if not self.referrers:
            self.referrers = []
        if not self.emails:
            self.emails = []
        if not self.sources:
            self.sources = []
        if not self.images:
            self.images = {}
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)        
        
    def process(self):
        score = 0
        score+=len(self.social_accounts) 
        score+=self.salary/10000 
        if self.amazon: 
            score += 2   
        score+=len(self.common_schools)
        score+=len(self.referrers)
        score+=len(self.emails)
        score+=len(self.sources)
        score+=len(self.images)
        if 'linkedin' in self.sources: 
            score+=6
        self.logger.info("Social accounts: %d, salary: %d, common schools: %d, referrers: %d, emails: %d, sources: %d, images: %d", len(self.social_accounts), self.salary, len(self.common_schools), len(self.referrers), len(self.emails), len(self.sources), len(self.images))
        return score
