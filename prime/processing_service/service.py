import hashlib
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

    def multiprocess(self):
        self.logger.info('Starting MultiProcess: %s', self.__class__.__name__)
        self.pool = multiprocessing.Pool(self.pool_size)
        self.output = self.pool.map(self.wrapper, self.data)
        self.pool.close()
        self.pool.join()
        self.logger.info('Ending MultiProcess: %s', self.__class__.__name__)
        return self.output

    def process(self):
        self.logger.info('Starting Process: %s', self.__class__.__name__)
        for person in self.data:
            person = self.wrapper(person)
            self.output.append(person)
        self.logger.info('Ending Process: %s', self.__class__.__name__)
        return self.output



