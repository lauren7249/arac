import web
import random
import getpass
import argparse
import datetime
import time

import tinys3, os, boto
from boto.s3.key import Key
from prime.utils import *
import web, re
from prime.utils.update_database_from_dict import *
from prime.prospects.get_prospect import get_session
from consume.consumer import *

session = get_session()

web.config.debug = False
urls = (
    '/select', 'select',
    '/process_chrome_ext_url/url=(.+)', 'process_chrome_ext_url',
    '/process_chrome_ext_content/url=(.+)', 'process_chrome_ext_content',
    '/log_uploaded/url=(.+)', 'log_uploaded'
)

app = web.application(urls, globals())
web_session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})

bucket_name='chrome-ext-uploads'

def get_bucket():
    s3conn = boto.connect_s3(os.getenv("AWS_ACCESS_KEY_ID_PVLL"), os.getenv("AWS_SECRET_ACCESS_KEY_PVLL"))
    return s3conn.get_bucket(bucket_name)

def process_content(content):
	if content is None: return None
	info = parse_html(content)	
	if info.get("complete") and info.get("success"):
		new_prospect = insert_linkedin_profile(info, session)
		return new_prospect.id
	else:
		return None

def process_url(url):
    bucket = get_bucket()
    try:
    	key = Key(bucket)
    	key.key = url
    	content = key.get_contents_as_string()	
    	return content
    except:
		return None

class log_uploaded:
    def GET(self, url):
        return r.rpush("chrome_uploads",re.sub(";","/",url))

class select:
    def GET(self):
        return r.srandmember("urls")

class process_chrome_ext_content:
    def POST(self):
		content = web.data()
		return process_content(content)       

class process_chrome_ext_url:
    def GET(self, url):
    	content = process_url(url)
    	return process_content(content)

if __name__ == "__main__":
    app.run()

