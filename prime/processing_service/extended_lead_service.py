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
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)      
        super(ExtendedLeadService, self).__init__(client_data, data, *args, **kwargs)  
        self.user = self._get_user()  

    def multiprocess(self):
        return self.process()
        
    def process(self):
        self.logstart()
        try:
            self.data = self._get_qualifying_info() 
            locations = [record.get("location_coordinates",{}).get("latlng") for record in self.data]           
            for person in self.data:
                if not person.get("extended"):
                    person["extended"] = False
                    self.output.append(person)
                    continue
                if self._valid_lead(person):
                    self.output.append(person)
                else:
                    self.bad_leads.append(person)
            #self.output = self.user.refresh_hiring_screen_data(self.output)                  
        except:
            self.logerror()
        self.logend()
        return self.output
