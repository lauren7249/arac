import requests
import boto
import boto.ec2
import lxml.html

AWS_ACCESS_KEY_ID = "AKIAIWG5K3XHEMEN3MNA"
AWS_SECRET_ACCESS_KEY = "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"

class aRequest(object):

    def __init__(self, url, *args, **kwargs):
        self.requests = requests
        self.url = url

    def _find_proxy(self):
        conn = boto.ec2.connect_to_region('us-east-1',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

        reservations = conn.get_all_instances(
                filters={"tag:Name" : "myName", "tag:Project" : "B"}
                )
        pass

    def _make_request(self):
        pass
