import os
from boto.s3.key import Key
import boto
from prime.utils.update_database_from_dict import insert_linkedin_profile
from prime.prospects.get_prospect import get_session

session = get_session()
s3conn = boto.connect_s3(os.environ["AWS_ACCESS_KEY_ID"], os.environ["AWS_SECRET_ACCESS_KEY"])
bucket = s3conn.get_bucket('parsed-webpages')

for key in bucket.list():
	info = eval(key.get_contents_as_string())
	insert_linkedin_profile(info, session)