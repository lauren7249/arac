import clearbit
import logging
import hashlib
import boto

from requests import HTTPError
from boto.s3.key import Key

from lead_service import LeadService

class ExtendedLeadService(LeadService):
    """
    Expected input is JSON with all profiles, including extended
    Output is filtered to qualified leads only
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(ExtendedLeadService, self).__init__(client_data, data, *args, **kwargs)  
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)        
        

    def process(self):
        self.logger.info('Starting Process: %s', 'Extended Lead Service')
        self.data = self._get_qualifying_info() 
        for person in self.data:
            if not person.get("extended"):
                person["extended"] = False
                self.good_leads.append(person)
                continue
            salary = self._filter_salaries(person)
            location = self._filter_same_locations(person)
            if salary and location:
                self.good_leads.append(person)
            else:
                self.bad_leads.append(person)
        self.logger.info('Good Leads: %s', len(self.good_leads))
        self.logger.info('Bad Leads: %s', len(self.bad_leads))
        self.logger.info('Ending Process: %s', 'Extended Lead Service')
        return self.good_leads
