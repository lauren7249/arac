import requests
import json
import random
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
        """
        conn = boto.ec2.connect_to_region('us-east-1',
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        reservations = conn.get_all_instances(
                filters={"tag:Name" : "arequest"}
                )
        ip_addresses = [i.ip_address for reservation in reservations for i in
        reservation.instances]
        """
        ip_addresses = ['54.152.186.2', '54.152.181.248']
        return random.choice(ip_addresses)

    def _make_request(self):
        url = self._find_proxy()
        content = self.requests.get("http://" + url + ":9090/proxy?url=" + self.url)
        return json.loads(content.content)

    def get(self):
        return self._make_request()
