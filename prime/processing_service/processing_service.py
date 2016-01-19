import os, sys, traceback
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
from prime import config

from service import Service
from cloudsponge_service import CloudSpongeService
from person_service import PersonService
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
from prime.processing_service.saved_request import UserRequest
SAVE_OUTPUTS = False

#DO NOT REORDER THESE
FIRST_DEGREE_NETWORK = [CloudSpongeService, PersonService, LeadService]
FOR_NETWORK_SUMMARY = [AgeService, GenderService, CollegeDegreeService]
EXTENDED_NETWORK = [ExtendedProfilesService, ExtendedLeadService]
CONTACT_INFO = [SocialProfilesService, PhoneService]
WRAP_UP = [ProfileBuilderService, ScoringService, ResultService]

class ProcessingService(Service):

    def __init__(self, client_data, data, *args, **kwargs):
        self.web_url = config[os.getenv('AC_CONFIG', 'default')].BASE_URL
        self.client_data = client_data
        self.data = data
        self.output = []
        user_request = UserRequest(client_data.get("email"),type='hiring-screen-data')
        self.saved_data = user_request.lookup_data()            
        if self.saved_data:     
            self.data = self.saved_data       
        if client_data.get("hired"):
            if self.saved_data:
                CLASS_LIST = CONTACT_INFO + WRAP_UP
            else:
                CLASS_LIST = FIRST_DEGREE_NETWORK + FOR_NETWORK_SUMMARY + EXTENDED_NETWORK + CONTACT_INFO + WRAP_UP
        else:
            if self.saved_data:
                CLASS_LIST = WRAP_UP
            else:
                CLASS_LIST = FIRST_DEGREE_NETWORK + FOR_NETWORK_SUMMARY + EXTENDED_NETWORK +  WRAP_UP
        SERVICES = OrderedDict()
        for CLASS in CLASS_LIST:
            SERVICES[str(CLASS).split(".")[-1].split("'")[0]] = CLASS
        self.services = SERVICES
        self.completed_services = {}
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.start = time.time()
        super(ProcessingService, self).__init__(*args, **kwargs)

    def _validate_data(self):
        if self.saved_data:
            return True
        validated_data = []
        required_client_keys = ["email","location","url","first_name","last_name"]
        for key in required_client_keys:
            if not self.client_data.get(key):
                self.logger.error("Missing Key:{}".format(key))
                return False
        for item in self.data:
            if item.get("contact"):
                validated_data.append(item)
            else:
                self.logger.error("Missing Key Contact For:{}".format(item))
                return False
        self.data = validated_data
        return True

    def process(self):
        self.logstart()
        if not self._validate_data():
            self.logerror()
            return []
        try:
            user = self._get_user()
            if user and self.client_data.get("hired"):
                user.p200_started = True
                self.session.add(user)
                self.session.commit()                
            self.logger.info('Data Valid')
            for key, _ in self.services.iteritems():
                if self.output:
                    service = self.services[key](
                            self.client_data,
                            self.output)
                else:
                    service = self.services[key](
                            self.client_data,
                            self.data)
                self.output = service.multiprocess()
                if SAVE_OUTPUTS:
                    save_output(self.output, self.client_data.get("email"), service.__class__.__name__)
            end = time.time()
            self.logger.info('Total Run Time: %s', end - self.start)
            env = Environment()
            env.loader = FileSystemLoader("prime/templates")
            if self.client_data.get("hired"):
                subject = "Your P200 List is ready!"
                to_email = self.client_data.get("email")
                tmpl = env.get_template('emails/p200_done.html')
                name = self.client_data.get("first_name")
            else:
                name = "{} {}".format(self.client_data.get("first_name"), \
                    self.client_data.get("last_name"))
                subject = "{}'s Hiring Screen is ready!".format(name)
                to_email = self.client_data.get("to_email")
                tmpl = env.get_template('emails/network_summary_done.html')        
            if user:
                body = tmpl.render(url=self.web_url, name=name, agent_id=user.user_id)
                sendgrid_email(to_email, subject, body)
                self.logger.info("{}'s stats for hired={}".format(self.client_data.get("email"), self.client_data.get("hired")))
                self.logger.info(unicode(json.dumps(user.statistics(), ensure_ascii=False)))                
            self.logend()
            return self.output
        except:
            self.logerror()

def save_output(output, user_email, service):
    _file = open("temp_data/{}_{}.txt".format(user_email, service), "w+")
    try:
        _file.write(output)
    except:
        _file.write(unicode(json.dumps(output, ensure_ascii=False)))
    _file.close()

if __name__ == '__main__':
    _file = open('data/bigtext.json', 'r')
    data = json.loads(_file.read().decode("utf-8-sig"))
    #shuffle(data)
    data = data[:19]
    #user = User("James","Johnson","jamesjohnson11@gmail.com", "password")
    client_data = { "first_name":"James","last_name":"Johnson", "email":"jamesjohnson11@gmail.com",
                    "location":"New York, New York","url":"http://www.linkedin.com/in/jamesjohnsona", "hired":False, "to_email":"laurentracytalbot@gmail.com"}
    logger.info("Input: {}".format(data))
    processing_service = ProcessingService(
            client_data = client_data,
            data=data)
    processing_service.process()
