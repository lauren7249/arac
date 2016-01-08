import logging
import hashlib
import boto
import lxml.html
import re
import dateutil
from boto.s3.key import Key
import multiprocessing
from service import Service, S3SavedRequest
from constants import GLOBAL_HEADERS
from clearbit_service_webhooks import ClearbitPersonService
from pipl_service import PiplService
from linkedin_service_crawlera import LinkedinService
#PiplService, ClearbitPersonService, LinkedinService

class PersonService(Service):
    """
    Expected input is JSON with emails
    Output is going to have linkedin profiles
    """

    def __init__(self, client_data, data, *args, **kwargs):
        super(PersonService, self).__init__(*args, **kwargs)
        self.client_data = client_data
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
    def multiprocess(self):
        self.logstart()
        self.service = PiplService(self.client_data, self.data)
        self.data = self.service.multiprocess()
        self.service = ClearbitPersonService(self.client_data, self.data)
        self.data = self.service.multiprocess()
        self.service = LinkedinService(self.client_data, self.data)
        self.output = self.service.multiprocess()        
        self.logend()
        return self.output

    def process(self):
        self.logstart()
        self.service = PiplService(self.client_data, self.data)
        self.data = self.service.process()
        self.service = ClearbitPersonService(self.client_data, self.data)
        self.data = self.service.process()
        self.service = LinkedinService(self.client_data, self.data)
        self.output = self.service.process()    
        self.logend()
        return self.output
