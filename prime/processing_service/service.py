import hashlib
from raven import Client

import sys
import os
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
from prime.users.models import User
from prime import create_app
from flask.ext.sqlalchemy import SQLAlchemy
try:
    app = create_app(os.getenv('AC_CONFIG', 'testing'))
    db = SQLAlchemy(app)
    session = db.session
except Exception, e:
    exc_info = sys.exc_info()
    traceback.print_exception(*exc_info)
    exception_str = traceback.format_exception(*exc_info)
    if not exception_str: exception_str=[""]
    print "ERROR: " + str(e)
    print "ERROR: " + "".join(exception_str)
    from prime import db
    session = db.session

reload(sys)
sys.setdefaultencoding('utf-8')

class Service(object):

    def __init__(self, input_data):
        self.pool_size = 10
        self.session = session
        self.input_data = input_data if input_data else {}
        self.client_data = self.input_data.get("client_data",{})
        self.data = self.input_data.get("data",[])
        self.excluded = self.input_data.get("excluded",[])
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _get_user(self):
        if self.client_data:
            user = self.session.query(User).filter_by(email=self.client_data.get("email","")).first()
            return user
        return None

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
        self.logger.info('Starting Process: %s with %d exclusions', self.__class__.__name__, len(self.excluded))

    def logend(self):
        self.logger.info('Ending Process: %s with %d outputs', self.__class__.__name__, len(self.output))
        self.logger.info('Ending Process: %s with %d exclusions', self.__class__.__name__, len(self.excluded))

    def logerror(self):
        exc_info = sys.exc_info()
        traceback.print_exception(*exc_info)
        exception_str = traceback.format_exception(*exc_info)
        if not exception_str: exception_str=[""]
        self.logger.error('Error in process {}: {}'.format(self.__class__.__name__,exception_str))
        client = Client('https://97521d50b8d647d2b25d7a29f4895ce1:7cd28a9ea427402987b40b1a08b834de@app.getsentry.com/74764')
        client.captureMessage('Error in process {}: {}'.format(self.__class__.__name__,exception_str))
        sendgrid_email('processing_script_error@advisorconnect.co','failed p200',"{}'s p200 failed during {} at {} outputs, with error {}".format(self.client_data.get("email"), self.__class__.__name__, str(len(self.output)), "\n".join(exception_str)), ccs=['jamesjohnson11@gmail.com'])

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
        return {"data":self.output, "client_data":self.client_data, "excluded":self.excluded}

    def process(self):
        self.logstart()
        try:
            for person in self.data:
                person = self.wrapper(person)
                self.output.append(person)
        except:
            self.logerror()
        self.logend()
        return {"data":self.output, "client_data":self.client_data, "excluded":self.excluded}



