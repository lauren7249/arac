import hashlib
import sys
import traceback
from prime.utils.email import sendgrid_email
import logging
import requests
import boto
from dateutil.parser import parser
import datetime
from boto.s3.key import Key
import multiprocessing
from constants import GLOBAL_HEADERS
import dateutil
from pipl_request import PiplRequest
from person_request import PersonRequest
from saved_request import S3SavedRequest

reload(sys) 
sys.setdefaultencoding('utf-8')

class Service(object):

    def __init__(self):
        self.pool_size = 10

    def _dedupe_profiles(self, profiles):
        if not profiles:
            return []
        linkedin_ids = set()
        deduped = []
        for profile in profiles:
            id = profile.get("linkedin_id")
            if id in linkedin_ids:
                continue
            linkedin_ids.add(id)
            deduped.append(profile)
        return deduped

    def logstart(self):
        self.logger.info('Starting Process: %s with %d inputs', self.__class__.__name__, len(self.data))

    def logend(self):
        self.logger.info('Ending Process: %s with %d outputs', self.__class__.__name__, len(self.output))

    def logerror(self):
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        exception_str = traceback.format_exception(*exc_info)
        if not exception_str: exception_str=[""]
        sendgrid_email('lauren@advisorconnect.co','failed p200',"{}'s p200 failed during {} at {} outputs, with error {}".format(self.client_data.get("email"), self.__class__.__name__, str(len(self.output)), "\n".join(exception_str)), ccs=['jamesjohnson11@gmail.com'])          
            
    def multiprocess(self):
        self.logstart()
        try:
            self.pool = multiprocessing.Pool(self.pool_size)
            self.output = self.pool.map(self.wrapper, self.data)
            self.pool.close()
            self.pool.join()
        except:
            self.logerror()
        self.logend()
        return self.output

    def process(self):
        self.logstart()
        try:
            for person in self.data:
                person = self.wrapper(person)
                self.output.append(person)
        except:
            self.logerror()
        self.logend()
        return self.output



