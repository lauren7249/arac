import logging

import boto
from boto.s3.key import Key

from service import S3SavedRequest

class UrlValidatorRequest(S3SavedRequest):

    """
    Given a url, this will return a boolean as to the validity, saving them to S3 as well
    """

    def __init__(self, url, is_image=False):
        super(UrlValidatorRequest, self).__init__()
        self.url = url
        self.is_image = is_image
        if not self.is_image:
            self.content_type ='text/html'
        else:
            ext = self.url.split(".")[-1]
            if ext == 'png':
                self.content_type = 'image/png'
            else:
                self.content_type = 'image/jpeg'
            s3conn = boto.connect_s3("AKIAIXDDAEVM2ECFIPTA", "4BqkeSHz5SbcAyM/cyTBCB1SwBrB9DDu0Ug/VZaQ")
            self.bucket= s3conn.get_bucket("public-profile-photos")

    def process(self):
        html = self._make_request(content_type =self.content_type , bucket=self.bucket)
        if len(html) > 0 and html != '{"status_code":404}':
            if self.is_image:
                return self.boto_key.generate_url(expires_in=0, query_auth=False)
            else:
                return self.url
        return None
