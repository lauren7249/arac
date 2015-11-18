import hashlib
import logging
import time
import sys
import os
import boto
from boto.s3.key import Key

from requests import session
from service import Service, S3SavedRequest
from constants import SCRAPING_API_KEY, new_redis_host, new_redis_port, \
new_redis_password, new_redis_dbname

from linkedin_parser import parse_html

class LinkedinService(Service):

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(LinkedinService, self).__init__(*args, **kwargs)

    def dispatch(self):
        pass

    def _get_redis():
        pool = redis.ConnectionPool(host=new_redis_host, port=new_redis_port, password=new_redis_password)
        r = redis.Redis(connection_pool=pool)
        return r

    @property
    def _s3_connection(self):
        s3conn = boto.connect_s3("AKIAIKCNCKG6RXJHWNFA", "GAwQwgy67hmp0lMShAV4O15zfDAfc8aKUoY7l2UC")
        return s3conn.get_bucket("aconn")

    def _lookup_s3(self, url):
        self.key = hashlib.md5(url).hexdigest()
        key = Key(self._s3_connection)
        key.key = self.key
        if key.exists():
            return key.get_contents_as_string()
        return None

    def _add_to_queue(self):
        pass

    def _get_linkedin_url(self, person):
        return person.values()[0].get("linkedin_urls")

    def process(self):
        self.logger.info('Starting Process: %s', 'Linkedin Service')
        for person in self.data:
            linkedin_url = self._get_linkedin_url(person)
            if linkedin_url:
                try:
                    request = LinkedinRequest(linkedin_url, person)
                    data = request.process()
                    self.output.append(data)
                except Exception, e:
                    self.logger.error("Linkedin Error: {}".format(e))
        self.logger.info('Ending Process: %s', 'Linkedin Service')
        return self.output


class LinkedinRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via PIPL
    """

    def __init__(self, query, data):
        linkedin_url = "http://proxy.crawlera.com:8010/fetch?url="
        self.data = data
        self.query = query
        self.api_url = "".join([linkedin_url, self.query])
        self.api_key = SCRAPING_API_KEY
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(LinkedinRequest, self).__init__()

    def _linkedin_request(self, max_retries):
        #TODO need a lot more logic here
        attempts = 0
        s = session()
        s.auth = (self.api_key, '',)
        s.headers.update({
            'User-Agent': 'python-scrapinghub/0',
            })
        s.stream = True
        s.prefetch = False
        while attempts < max_retries:
            attempts += 1
            result = s.get(self.api_url)
            if result.status_code == 200:
                return result.content
            time.sleep(5)
            self.logger.info('Linkedin Failure Count: %s', attempts)
        return None

    def _make_request(self):
        self.key = hashlib.md5(self.query).hexdigest()
        key = Key(self._s3_connection)
        key.key = self.key
        if key.exists():
            html = key.get_contents_as_string()
        else:
            html = self._linkedin_request(max_retries=5)
            key.content_type = 'text/html'
            key.set_contents_from_string(html)
        return html

    def process(self):
        self.logger.info('Linkedin Request: %s', 'Starting')
        html = self._make_request()
        info = parse_html(html)
        self.data.update({"linkedin_data": info})
        return self.data



