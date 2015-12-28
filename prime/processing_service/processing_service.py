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
#RUN_EXTENDED = (sys.argv[-1] == "1")
RUN_EXTENDED = True
class ProcessingService(Service):

    def __init__(self, client_data, data, *args, **kwargs):
        #DO NOT REORDER THESE 
        if client_data.get("hired"):
            if RUN_EXTENDED:
                CLASS_LIST = [CloudSpongeService, PiplService, ClearbitPersonService, LinkedinService, LeadService, ExtendedProfilesService, ExtendedLeadService, SocialProfilesService, LinkedinCompanyService, PhoneService,  AgeService, GenderService, CollegeDegreeService, ProfileBuilderService, ScoringService, ResultService]
            else:
                CLASS_LIST = [CloudSpongeService, PiplService, ClearbitPersonService, LinkedinService, LeadService, SocialProfilesService, LinkedinCompanyService, PhoneService,  AgeService, GenderService, CollegeDegreeService, ProfileBuilderService, ScoringService, ResultService]   
        else:
            if RUN_EXTENDED:
                CLASS_LIST = [CloudSpongeService, PiplService, ClearbitPersonService, LinkedinService, LeadService, LinkedinCompanyService, AgeService, GenderService, CollegeDegreeService, ProfileBuilderService, ScoringService, ExtendedProfilesService, ExtendedLeadService, ResultService]
            else:
                CLASS_LIST = [CloudSpongeService, PiplService, ClearbitPersonService, LinkedinService, LeadService, LinkedinCompanyService, AgeService, GenderService, CollegeDegreeService, ProfileBuilderService, ScoringService, ResultService]   
        SERVICES = OrderedDict()    
        for CLASS in CLASS_LIST:
            SERVICES[str(CLASS).split(".")[-1].split("'")[0]] = CLASS  
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
                output = service.multiprocess()
                if SAVE_OUTPUTS:
                    save_output(output, self.client_data.get("email"), service.__class__.__name__)
            # if output:
            #     print json.dumps(output, sort_keys=True, indent=4)
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
    data = data[:9999]
    client_data = { "first_name":"Lauren","last_name":"Talbot", "email":"laurentracytalbot@gmail.com",
                    "location":"New York, New York","url":"http://www.linkedin.com/in/laurentalbotnyc", "hired":True}  
    logger.info("Input: {}".format(data))
    processing_service = ProcessingService(
            client_data = client_data,
            data=data)
    processing_service.process()
