import selenium
import boto
from boto.manage.cmdshell import sshclient_from_instance


class SeleniumTest(object):

    def __init__(url, *args, **kwargs):
        self.url = url
        self.AWS_ACCESS_KEY = 'AKIAJGWKMPXLQPGWSGTQ'
        self.AWS_SECRET_KEY = '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'

    def _new_machine(self):
        conn = boto.ec2.connect_to_region('us-east-1a')
        conn.run_instances(ami, instance_type='m1.large', key_name='ec2-keypair', placement='us-east-1a')


