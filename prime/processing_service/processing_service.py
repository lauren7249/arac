import os, sys
import csv
import time
import json
import logging
from collections import OrderedDict
from flask import render_template
from jinja2 import FileSystemLoader
from jinja2.environment import Environment
from random import shuffle
BASE_DIR = os.path.dirname(__file__)
PRIME_DIR =  os.path.split(os.path.split(BASE_DIR)[0])[0]
sys.path.append(PRIME_DIR)
logger = logging.getLogger(__name__)

from prime.utils.email import sendgrid_email

from service import Service
from cloudsponge_service import CloudSpongeService
from clearbit_service_webhooks import ClearbitPersonService
from pipl_service import PiplService
from linkedin_service_crawlera import LinkedinService
from linkedin_company_service import LinkedinCompanyService
from age_service import AgeService
from gender_service import GenderService
from college_degree_service import CollegeDegreeService
from lead_service import LeadService
from profile_builder_service import ProfileBuilderService
from phone_service import PhoneService
from results_service import ResultService
from social_profiles_service import SocialProfilesService
from scoring_service import ScoringService
from extended_profiles_service import ExtendedProfilesService
from extended_lead_service import ExtendedLeadService
SAVE_OUTPUTS = False
RUN_EXTENDED = (sys.argv[-1] == "1")
#DO NOT REORDER THESE 
SERVICES = OrderedDict()
SERVICES['cloud_sponge'] = CloudSpongeService
SERVICES['pipl_serice'] =  PiplService
SERVICES['clearbit_service'] =  ClearbitPersonService
SERVICES['linkedin_service'] = LinkedinService
SERVICES['lead_service'] = LeadService
#it goes much faster if you dont run extended
if RUN_EXTENDED:
    logger.info("RUNNING extended network for comprehensive check!!!!")
    SERVICES['extended_profiles_service'] = ExtendedProfilesService
    SERVICES['extended_lead_service'] = ExtendedLeadService
else:
    logger.info("SKIPPING extended network for speed!!!!")
SERVICES['social_profiles_service'] = SocialProfilesService
SERVICES['linkedin_company_service'] = LinkedinCompanyService
SERVICES['phone_service'] = PhoneService
SERVICES['age_service'] = AgeService
SERVICES['gender_service'] = GenderService
SERVICES['college_degree_service'] = CollegeDegreeService
SERVICES['profile_builder_service'] = ProfileBuilderService
SERVICES['scoring_service'] = ScoringService
SERVICES['results_service'] = ResultService

class ProcessingService(Service):

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
        self.data = data
        self.services = SERVICES
        self.completed_services = {}
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.start = time.time()
        super(ProcessingService, self).__init__(*args, **kwargs)

    def _validate_data(self):
        validated_data = []
        required_client_keys = ["email","location","url","first_name","last_name"]
        for key in required_client_keys:
            if not self.client_data.get(key):
                return False
        for item in self.data:
            if item.get("contact"):
                validated_data.append(item)
            else:
                return False
        self.data = validated_data
        return True

    def process(self):
        self.logger.info('Starting Process: %s', self.client_data)
        output = None
        if self._validate_data():
            self.logger.info('Data Valid')
            for key, _ in self.services.iteritems():
                if output is not None:
                    service = self.services[key](
                            self.client_data,
                            output)
                else:
                    service = self.services[key](
                            self.client_data,
                            self.data)
                output = service.process()
                if SAVE_OUTPUTS:
                    save_output(output, self.client_data.get("email"), service.__class__.__name__)

        end = time.time()
        self.logger.info('Total Run Time: %s', end - self.start)
        env = Environment()
        env.loader = FileSystemLoader("prime/templates")
        tmpl = env.get_template('emails/done.html')
        body = tmpl.render()
        subject = "Your p200 List is ready!"
        to_email = self.client_data.get("email")
        sendgrid_email(to_email, subject, body)
        return output

def save_output(output, user_email, service):
    _file = open("temp_data/{}_{}.txt".format(user_email, service), "w+")
    try:
        _file.write(output)
    except:
        _file.write(json.dumps(output))
    _file.close()

if __name__ == '__main__':
    _file = open('data/bigtext.json', 'r')
    data = json.loads(_file.read())
    shuffle(data)
    data = data[:10]
    client_data = { "first_name":"Lauren","last_name":"Talbot", "email":"laurentracytalbot@gmail.com",
                    "location":"New York, New York","url":"http://www.linkedin.com/in/laurentalbotnyc"}  
    logger.info("Input: {}".format(data))
    processing_service = ProcessingService(
            client_data = client_data,
            data=data)
    processing_service.process()
