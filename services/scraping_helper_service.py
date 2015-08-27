import web
import random
import getpass
import argparse
import datetime
import time
from random import shuffle

import tinys3, os, boto
from boto.s3.key import Key
from prime.utils import *
import web, re
from prime.utils.update_database_from_dict import insert_linkedin_profile
from prime.prospects.get_prospect import get_session
from consume.consumer import *
from prime.prospects.models import CloudspongeRecord
session = get_session()

web.config.debug = False
urls = (
    '/select/n=(.+)', 'select',
    '/process_chrome_ext_url/url=(.+)', 'process_chrome_ext_url',
    '/process_chrome_ext_content/url=(.+)', 'process_chrome_ext_content',
    '/log_uploaded/url=(.+)', 'log_uploaded',
    '/add', 'add'
)

app = web.application(urls, globals())
web_session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})

bucket = get_bucket(bucket_name='chrome-ext-uploads')

def url_to_s3_key(url):
	fn = url.replace("https://","").replace("http://", "").replace("/","-") + ".html"
	return fn
	
def process_content(content, source_url=None):
    if content is None: return None
    info = parse_html(content)	
    if info.get("success") and info.get("complete"):
        if source_url is not None: info["source_url"] = source_url
        new_prospect = insert_linkedin_profile(info, session)
        return new_prospect.id
    else: return None

def process_url(url):
    try:
    	key = Key(bucket)
    	key.key = url
    	content = key.get_contents_as_string()	
    	return content
    except:
		return None

class log_uploaded:
    def GET(self, url):
        real_url = url.replace(";","/").replace("`","?")
        r.srem("urls", real_url)
        r.sadd("chrome_uploads",real_url)
        return url
# http://www.google.com/search?q=site:www.linkedin.com+John+Lamont+Baritelle+California&es_sm=91&ei=NZxTVY_lB8mPyATvpoGACg&sa=N&num=100&start=0
# http://www.google.com/search?q=site%3Awww.linkedin.com+John+Lamont+Baritelle+California&es_sm=91&ei=NZxTVY_lB8mPyATvpoGACg&sa=N&num=100&start=0
class select:
    def GET(self, n):
        all = list(r.smembers("urls"))
        shuffle(all)
        return "\n".join(all[0:int(n)])

class process_chrome_ext_content:
    def POST(self):
		content = web.data()
		return process_content(content)       

class process_chrome_ext_url:
    def GET(self, url):
    	content = process_url(url)
    	return process_content(content)

class add:
    def POST(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')      
        web.header('Access-Control-Allow-Headers', '*')
        web.header('Access-Control-Allow-Methods','*')
        i = web.data()
        for record in json.loads(i):
            owner = record.get("contacts_owner",{})
            contact = record.get("contact",{})
            r = CloudspongeRecord(owner=owner, contact=contact)
            session.add(r)
        session.commit()
        return "good"
if __name__ == "__main__":
    app.run()

