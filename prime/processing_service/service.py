import hashlib
import logging
import requests
import boto

from boto.s3.key import Key

from constants import AWS_KEY, AWS_SECRET, AWS_BUCKET

class Service(object):

    def __init__(self):
        pass

    def _validate_data(self):
        return False

    def process(self):
        pass

    def dispatch(self):
        pass

class TemporaryProspect(object):
    pass

class S3SavedRequest(object):

    """
    Instead of just making a request, this saves the exact request to s3 so we
    don't need to make it again
    """

    def __init__(self, *args, **kwargs):
        self.url = None
        self.key = None

    @property
    def _s3_connection(self):
        s3conn = boto.connect_s3("AKIAIKCNCKG6RXJHWNFA", "GAwQwgy67hmp0lMShAV4O15zfDAfc8aKUoY7l2UC")
        return s3conn.get_bucket("aconn")

    def _make_request(self):
        self.key = hashlib.md5(self.url).hexdigest()
        key = Key(self._s3_connection)
        key.key = self.key
        if key.exists():
            html = key.get_contents_as_string()
        else:
            response = requests.get(self.url)
            html = response.content
            key.content_type = 'text/html'
            key.set_contents_from_string(html)
        return html

