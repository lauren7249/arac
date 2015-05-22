
import boto
from boto.s3.key import Key
import re

def get_bucket():
    s3conn = boto.connect_s3("AKIAIXDDAEVM2ECFIPTA","4BqkeSHz5SbcAyM/cyTBCB1SwBrB9DDu0Ug/VZaQ")
    return s3conn.get_bucket('parsed-webpages')

bucket = get_bucket()

def upload(d):
	key = Key(bucket)
	key.key = re.sub("/","_",d.get("source_url"))
	key.set_contents_from_string(str(d))