import clearbit
import logging
import hashlib
import boto

from requests import HTTPError
from boto.s3.key import Key

from service import Service, S3SavedRequest

class ClearbitService(Service):
    """
    Expected input is JSON of unique email addresses from cloudsponge
    Output is going to be social accounts and Linkedin IDs via PIPL
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(ClearbitService, self).__init__(*args, **kwargs)

    def dispatch(self):
        pass

    def _exclude_person(self, person):
        if len(person.values()) > 0:
            if person.values()[0].get("linkedin_urls"):
                return True
                #return False
        return False

    def process(self):
        self.logger.info('Starting Process: %s', 'Clearbit Service')
        for person in self.data:
            if self._exclude_person(person):
                self.output.append(person)
            else:
                email = person.keys()[0]
                request = ClearbitRequest(email)
                data = request.process()
                self.output.append(data)
        self.logger.info('Ending Process: %s', 'Clearbit Service')
        return self.output


class ClearbitRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via Clearbit
    """

    def __init__(self, query, type='email'):
        self.clearbit = clearbit
        self.clearbit.key='f2512e10a605e3dcaff606205dbd3758'
        self.query = query
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _make_request(self):
        self.key = hashlib.md5(self.query).hexdigest()
        key = Key(self._s3_connection)
        key.key = self.key
        if key.exists():
            self.logger.info('Make Request: %s', 'Get From S3')
            html = key.get_contents_as_string()
        else:
            try:
                self.logger.info('Make Request: %s', 'Query Clearbit')
                person = clearbit.Person.find(email=self.query, stream=True)
            except HTTPError as e:
                self.logger.info('Clearbit Fail')
                person = None
            if person:
                #TODO, this doesn't work
                try:
                    key.content_type = 'text/html'
                    key.set_contents_from_string(person)
                except:
                    pass
        return person


    def _social_accounts(self, clearbit_json):
        social_accounts = []
        if not clearbit_json:
            return social_accounts
        for key in clearbit_json.keys():
            if isinstance(clearbit_json[key], dict) and clearbit_json[key].get('handle'):
                handle = clearbit_json[key].get("handle")
                if key=='angellist':
                    link = "https://angel.co/" + handle
                elif key=='foursquare':
                    link = "https://" + key + ".com/user/" + handle
                elif key=='googleplus':
                    link = "https://plus.google.com/" + handle
                elif key=='twitter':
                    link = "https://twitter.com/" + handle
                elif key=='facebook':
                    link = "https://facebook.com/" + handle
                elif key=='linkedin':
                    link = "https://www." + key + ".com/" + handle
                else:
                    link = "https://" + key + ".com/" + handle
                social_accounts.append(link)
        return social_accounts

    def _linkedin_url(self, social_accounts):
        for record in social_accounts:
            if "linkedin.com" in record:
                return record
        self.logger.warn('Linkedin: %s', 'Not Found')
        return None

    def process(self):
        self.logger.info('Clearbit Request: %s', 'Starting')
        response = {}
        clearbit_json = self._make_request()
        social_accounts = self._social_accounts(clearbit_json)
        linkedin_url = self._linkedin_url(social_accounts)
        data = {"social_accounts": social_accounts,
                "linkedin_urls": linkedin_url}
        response[self.query] = data
        return response




