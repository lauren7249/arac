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

HIRED = False

def wrapper(person):
    try:
        global HIRED
        person["wealthscore"] = WealthScoreRequest(person).process()
        if HIRED:
            person["lead_score"] = LeadScoreRequest(person).process()    
        return person
    except Exception, e:
        print __name__ + str(e)
        return person

class ScoringService(Service):
    """
    Expected input is JSON with fully built profiles
    Output is going to be existig data enriched with wealth scores
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(ScoringService, self).__init__(*args, **kwargs)
        self.client_data = client_data
        self.data = data
        self.output = []
        self.wrapper = wrapper
        global HIRED
        HIRED = self.client_data.get("hired")
        self.hired = self.client_data.get("hired")
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
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
            if self.hired:  
                self.output = self.compute_stars()
        except:
            self.logerror()
        self.logend()
        return self.output

    def process(self):
        self.logstart()
        try:
            for person in self.data:
                person = self.wrapper(person)
                self.output.append(person)
            if self.hired:  
                self.output = self.compute_stars()
        except:
            self.logerror()
        self.logend()
        return self.output

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
        except:
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
        self.social_accounts = person.get("social_accounts",[])
        self.salary = max(self.indeed_salary, self.glassdoor_salary)
        if not self.salary:
            self.salary = -1
        self.common_schools = person.get("common_schools",[])
        self.referrers = person.get("referrers",[])
        self.emails = person.get("email_addresses",[])
        self.sources = person.get("sources",[])
        self.images = person.get("profile_image_urls",[])
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
