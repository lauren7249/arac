import hashlib
import json
import logging
import requests
import boto
import dateutil
import datetime
from boto.s3.key import Key
from helper import uu, resolve_email
from constants import AWS_KEY, AWS_SECRET, AWS_BUCKET, GLOBAL_HEADERS
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

class S3SavedRequest(object):

    """
    Instead of just making a request, this saves the exact request to s3 so we
    don't need to make it again

    """

    def __init__(self):
        self.url = None
        self.headers = GLOBAL_HEADERS
        self.key = None
        S3_BUCKET = boto.connect_s3(AWS_KEY, AWS_SECRET).get_bucket(AWS_BUCKET)
        self.bucket = S3_BUCKET
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _make_request(self, content_type = 'text/html', bucket=None, proxies=None):
        try:
            self.key = hashlib.md5(self.url).hexdigest()
        except Exception, e:
            print e
            self.key = hashlib.md5(uu(self.url)).hexdigest()
        if not bucket:
            bucket = self.bucket
        self.boto_key = Key(bucket)
        self.boto_key.key = self.key
        if self.boto_key.exists():
            self.logger.info("Getting from S3")
            html = self.boto_key.get_contents_as_string()
            if html:
                return html
        try:
            self.logger.info("Hitting url: {}".format(self.url))
            self.response = requests.get(self.url, headers=self.headers, proxies=proxies)
            if self.response.status_code != 404:
                html = self.response.content
            else:
                html = '{"status_code":404}'
        except:
            html = ''
        self.boto_key.content_type = content_type
        self.boto_key.set_contents_from_string(html)
        return html


class UserRequest(S3SavedRequest):

    def __init__(self, email, type='p200-', number=0):
        super(UserRequest, self).__init__()
        email = resolve_email(email)
        roman = "".join(['1' for b in xrange(0, number)])
        self.url = "{}{}{}".format(type,email,roman)
        try:
            self.key = hashlib.md5(self.url).hexdigest()
        except Exception, e:
            self.key = hashlib.md5(uu(self.url)).hexdigest()
        self.boto_key = Key(self.bucket)
        self.boto_key.key = self.key

    def _make_request(self, data, content_type = 'text/html'):
        self.boto_key.content_type = content_type
        self.boto_key.set_contents_from_string(unicode(json.dumps(data, ensure_ascii=False)))
        return data

    def lookup_data(self):
        try:
            self.logger.info('Make Request: %s', 'Get From S3')
            html = self.boto_key.get_contents_as_string()
            entity = json.loads(html.decode("utf-8-sig"))
            return entity
        except:
            return []

