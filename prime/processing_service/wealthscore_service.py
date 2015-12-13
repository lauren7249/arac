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

class WealthScoreService(Service):
    """
    Expected input is JSON with profile info
    Output is going to be existig data enriched with wealth scores
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(WealthScoreService, self).__init__(*args, **kwargs)

    def process(self):
        for person in self.data:
            request = WealthScoreRequest(person)
            wealthscore = request.process()
            person["wealthscore"] = wealthscore
            self.output.append(person)
        return self.output

class WealthScoreRequest(S3SavedRequest):

    """
    Given a job, this will get a salary
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
        self.url = "http://www.shnugi.com/income-percentile-calculator/?min_age=18&max_age=100&income=" + str(self.max_salary)
        html = self._make_request()
        try:
            percentile = re.search('(?<=ranks at: )[0-9]+(?=(\.|\%))',html).group(0)
            return int(re.sub("[^0-9]","",percentile))    
        except:
            return None


