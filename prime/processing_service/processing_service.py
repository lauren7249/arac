import os, sys, traceback
import csv
import time
import json
import logging
from collections import OrderedDict
from jinja2 import FileSystemLoader
from jinja2.environment import Environment
from random import shuffle
BASE_DIR = os.path.dirname(__file__)
PRIME_DIR =  os.path.split(os.path.split(BASE_DIR)[0])[0]
sys.path.append(PRIME_DIR)
logger = logging.getLogger(__name__)

from flask import render_template

from prime.utils.email import sendgrid_email
from prime import config, db
from prime.users.models import User
from prime.managers.models import ManagerProfile
from service import Service
from saved_request import UserRequest
from cloudsponge_service import CloudSpongeService
from person_service import PersonService
from age_service import AgeService
from gender_service import GenderService
from college_degree_service import CollegeDegreeService
from lead_service import LeadService
from profile_builder_service import ProfileBuilderService
from phone_and_address_service import PhoneAndAddressService
from results_service import ResultService
from social_profiles_service import SocialProfilesService
from scoring_service import ScoringService
from extended_profiles_service import ExtendedProfilesService
from extended_lead_service import ExtendedLeadService

#DO NOT REORDER THESE
FIRST_DEGREE_NETWORK = [CloudSpongeService, PersonService, LeadService]
FOR_NETWORK_SUMMARY = [AgeService, GenderService, CollegeDegreeService]
EXTENDED_NETWORK = [ExtendedProfilesService, ExtendedLeadService]
CONTACT_INFO = [SocialProfilesService, PhoneAndAddressService]
WRAP_UP = [ProfileBuilderService, ScoringService, ResultService]

class ProcessingService(Service):

    def __init__(self, data, *args, **kwargs):
        super(ProcessingService, self).__init__(data, *args, **kwargs)
        self.web_url = config[os.getenv('AC_CONFIG', 'testing')].BASE_URL
        self.saved_data = []
        self.user = self._get_user()
        #to save the user time, we dont actually pass the array through when the user clicks upload. therefore, we grab it from S3 over here.
        if not self.data:
            if self.user:
                self.data, self.user = self.user.refresh_contacts(session=self.session)
            else:      
                user_request = UserRequest(self.client_data.get("email"))
                self.data = user_request.lookup_data()
            if self.data:
                self.input_data = {"client_data": self.client_data, "data":self.data}
                self.logger.info("Using saved data from upload")
        if self.user:
            self.saved_data = self.user.refresh_hiring_screen_data()
        if len(self.saved_data) < 50 :
            self.saved_data = None
        if self.saved_data:
            self.logger.info("Using saved data from last network analysis")
            self.data = self.saved_data
            self.input_data = {"client_data": self.client_data, "data":self.data}
        if self.client_data.get("hired"):
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
        self.start = time.time()


    def _validate_data(self):
        if self.saved_data:
            return True
        validated_data = []
        required_client_keys = ["email","location","first_name","last_name"]
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
            self.user = self._get_user()
            if self.user and self.client_data.get("hired"):
                self.user.p200_started = True
                self.session.add(self.user)
                self.session.commit()
            self.logger.info('Data Valid')
            for key, _ in self.services.iteritems():
                if key == self.services.keys()[0]:
                    service = self.services[key](self.input_data)
                else:
                    service = self.services[key](self.output_data)
                self.output_data = service.multiprocess()
            end = time.time()
            self.logger.info('Total Run Time: %s', end - self.start)
            if self.user and not self.client_data.get("suppress_emails"):
                env = Environment()
                env.loader = FileSystemLoader("prime/templates")
                manager = self.session.query(ManagerProfile).get(self.user.manager_id)
                if self.client_data.get("hired"):
                    subject = "Congratulations from {}".format(config[os.getenv('AC_CONFIG', 'testing')].OWNER)
                    to_email = self.client_data.get("email")
                    tmpl = env.get_template('emails/p200_done.html')
                    body = tmpl.render(manager=manager, agent=self.user,base_url=self.web_url, inviter=config[os.getenv('AC_CONFIG', 'testing')].OWNER)
                    sendgrid_email(to_email, subject, body, from_email=self.user.manager.user.email)
                else:
                    name = "{} {}".format(self.client_data.get("first_name"), \
                        self.client_data.get("last_name"))
                    subject = "{}'s Network Analysis is ready".format(name)
                    to_email = self.client_data.get("to_email")
                    tmpl = env.get_template('emails/network_summary_done.html')
                    body = tmpl.render(url=self.web_url, name=name, agent_id=self.user.user_id)
                    sendgrid_email(to_email, subject, body)
                    subject = "Your Network Analysis is ready to view"
                    to_email = self.client_data.get("email")
                    tmpl = env.get_template('emails/network_summary_done_agent.html')
                    body = tmpl.render(url=self.web_url, agent=self.user, manager=manager)
                    sendgrid_email(to_email, subject, body, from_email=manager.user.email)
            elif not self.user:
                self.logger.error("no user")
            #self.logger.info("{}'s stats for hired={}".format(self.client_data.get("email"), self.client_data.get("hired")))
            self.logend()
            return self.output
        except:
            self.logerror()

if __name__ == '__main__':
    _file = open('data/bigtext.json', 'r')
    # data = json.loads(_file.read().decode("utf-8-sig"))
    #shuffle(data)

    #user = User("James","Johnson","jamesjohnson11@gmail.com", "password")
    client_data = { "first_name":"Julia","last_name":"Karl", "email":"juliakarl2@gmail.com",
                    "location":"New York, New York","url":"http://www.linkedin.com/in/jukarl", "hired":False, "to_email":"jimmy@advisorconnect.co"}
    # logger.info("Input: {}".format(data))
    # data = data[:19]
    processing_service = ProcessingService({"client_data":client_data})
    processing_service.process()
