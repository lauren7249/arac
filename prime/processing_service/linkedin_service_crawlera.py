import hashlib
import logging
import time
import sys
import os
import sys
import boto
from boto.s3.key import Key
import json
import requests
import multiprocessing

from service import Service
from saved_request import S3SavedRequest
from person_request import PersonRequest
reload(sys)
sys.setdefaultencoding('utf-8')

def wrapper(person):
    try:
        linkedin_url = person.get("linkedin_url")
        if linkedin_url:
            linkedin_data = PersonRequest()._get_profile_by_any_url(linkedin_url)
            person["linkedin_data"] = linkedin_data
            return person
        # if "linkedin" in person.get("sources") and person.get("job_title"):
        #     print "no linkedin url found for {} | {} | {} | {}".format(person.get("first_name"),person.get("last_name"),person.get("job_title"),person.get("companies"))
        return person
    except Exception, e:
        print __name__ + ": " + str(e)
        return person
        
class LinkedinService(Service):
    '''
    Gets linkedin data and collapses by linkedin_id, merging the email addresses, images, and social acounts for the person, 
    as well as the cloudsponge sources from whence the person was obtained
    '''
    def __init__(self, data, *args, **kwargs):
        super(LinkedinService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper

