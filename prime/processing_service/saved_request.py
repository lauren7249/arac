import hashlib
import logging
import requests
import boto
from boto.s3.key import Key
from helper import uu
from constants import AWS_KEY, AWS_SECRET, AWS_BUCKET, GLOBAL_HEADERS
S3_BUCKET = boto.connect_s3(AWS_KEY, AWS_SECRET).get_bucket(AWS_BUCKET)
class S3SavedRequest(object):

    """
    Instead of just making a request, this saves the exact request to s3 so we
    don't need to make it again
    """

    def __init__(self):
        self.url = None
        self.headers = GLOBAL_HEADERS
        self.key = None
        self.bucket = S3_BUCKET

    def _make_request(self, content_type = 'text/html', bucket=None):
        try:
            self.key = hashlib.md5(self.url).hexdigest()
        except:
            self.key = hashlib.md5(uu(self.url)).hexdigest()
        if not bucket:
            bucket = self.bucket
        self.boto_key = Key(bucket)
        self.boto_key.key = self.key
        if self.boto_key.exists():
            html = self.boto_key.get_contents_as_string()
        else:
            try:
                self.response = requests.get(self.url, headers=self.headers)
                if self.response.status_code ==200:
                    html = self.response.content
                else:
                    html = ''                
            except:
                html = ''
            self.boto_key.content_type = content_type
            self.boto_key.set_contents_from_string(html)
        return html

