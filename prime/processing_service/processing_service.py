import csv
import time
import json
import logging
from collections import OrderedDict

from service import Service
from cloudsponge_service import CloudSpongeService
from clearbit_service import ClearbitService
from pipl_service import PiplService
from linkedin_service import LinkedinService
from glassdoor_service import GlassdoorService
from indeed_service import IndeedService
from lead_service import LeadService



SERVICES = OrderedDict()
SERVICES['cloud_sponge'] = CloudSpongeService
SERVICES['pipl_serice'] =  PiplService
SERVICES['clearbit_service'] =  ClearbitService
SERVICES['linkedin_service'] = LinkedinService
SERVICES['glassdoor_service'] = GlassdoorService
SERVICES['indeed_service'] = IndeedService
SERVICES['lead_service'] = LeadService

class ProcessingService(Service):

    # FIXME super __init__ not called
    # FIXME the variable "data" is already defined in the csv import and
    #       this data might lead to a hard to track down subtle error in the future
    #       I'd suggest renaming just to be safe
    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.services = SERVICES
        self.completed_services = {}
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.start = time.time()

    def _validate_data(self):
        self.logger.info('Data Valid')
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
        end = time.time()
        self.logger.info('Total Run Time: %s', end - self.start)
        return True

# FIXME "file" is a built-in python name you've overridden
if __name__ == '__main__':
    data = []
    file = csv.reader(open('data/test.csv', 'r'))
    for line in file:
        raw_json = json.loads(line[3])
        data.append(raw_json)
    processing_service = ProcessingService(
            user_email='jamesjohnson11@gmail.com',
            user_linkedin_url = "https://www.linkedin.com/in/jamesjohnsona",
            data=data)
    processing_service.process()
