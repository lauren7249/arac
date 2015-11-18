import os, sys
import csv
import time
import json
import logging
from collections import OrderedDict

BASE_DIR = os.path.dirname(__file__)
PRIME_DIR =  os.path.split(os.path.split(BASE_DIR)[0])[0]
sys.path.append(PRIME_DIR)

from service import Service
from cloudsponge_service import CloudSpongeService
from clearbit_service import ClearbitService
from pipl_service import PiplService
from linkedin_service import LinkedinService
from glassdoor_service import GlassdoorService
from indeed_service import IndeedService
from geocode_service import GeoCodingService
from lead_service import LeadService
#from extended_lead_service import ExtendedLeadService
from bloomberg_service import BloombergService
from results_service import ResultService

SAVE_OUTPUTS = False

SERVICES = OrderedDict()
SERVICES['cloud_sponge'] = CloudSpongeService
SERVICES['pipl_serice'] =  PiplService
SERVICES['clearbit_service'] =  ClearbitService
SERVICES['linkedin_service'] = LinkedinService
SERVICES['glassdoor_service'] = GlassdoorService
SERVICES['indeed_service'] = IndeedService
SERVICES['geocode_service'] = GeoCodingService
SERVICES['bloomberg_service'] = BloombergService
SERVICES['lead_service'] = LeadService
#SERVICES['extended_lead_service'] = ExtendedLeadService
SERVICES['results_service'] = ResultService

class ProcessingService(Service):

    # FIXME super __init__ not called
    # FIXME the variable "data" is already defined in the csv import and
    #       this data might lead to a hard to track down subtle error in the future
    #       I'd suggest renaming just to be safe
    def __init__(self, user_email, user_linkedin_url, csv_data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = csv_data
        self.services = SERVICES
        self.completed_services = {}
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.start = time.time()
        super(ProcessingService, self).__init__(*args, **kwargs)

    def _validate_data(self):
        self.logger.info('Data Valid')
        validated_data = []
        for item in self.data:
            validated_data.append(item.get("contact"))
        self.data = validated_data
        return True

    def dispatch(self):
        pass

    def process(self):
        d = {'user': self.user_email, 'linkedin_id': self.user_linkedin_url}
        self.logger.info('Starting Process: %s', d)
        output = None
        if self._validate_data():
            for key, _ in self.services.iteritems():
                if output:
                    service = self.services[key](
                            self.user_email,
                            self.user_linkedin_url,
                            output)
                else:
                    service = self.services[key](
                            self.user_email,
                            self.user_linkedin_url,
                            self.data)
                output = service.process()
                if SAVE_OUTPUTS:
                    save_output(output, self.user_email, service.__class__.__name__)

        end = time.time()
        self.logger.info('Total Run Time: %s', end - self.start)
        return True


def save_output(output, user_email, service):
    file = open("temp_data/{}_{}.txt".format(user_email, service), "w+")
    try:
        file.write(output)
    except:
        file.write(json.dumps(output))

    file.close()

# FIXME "file" is a built-in python name you've overridden
if __name__ == '__main__':
    data = []
    file = csv.reader(open('data/test.csv', 'r'))
    for line in file:
        raw_json = json.loads(line[3])
        new_json = {}
        new_json['contact'] = raw_json
        data.append(new_json)
    print data
    processing_service = ProcessingService(
            user_email='jamesjohnson11@gmail.com',
            user_linkedin_url = "https://www.linkedin.com/in/jamesjohnsona",
            csv_data=data)
    processing_service.process()
