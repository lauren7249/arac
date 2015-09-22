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
from consume.consumer import *
from prime.prospects.models import CloudspongeRecord, PhoneExport, session
from services.touchpoints_costs import *

web.config.debug = False
urls = (
    '/select/n=(.+)', 'select',
    '/log_uploaded/url=(.+)', 'log_uploaded',
    '/post_uploaded', 'post_uploaded',
    '/add', 'add',
    '/get_phone_export/id=(.+)', 'get_phone_export',
    '/calculate_costs', 'calculate_costs',
    '/get_my_total/user_id=(.+)', 'get_my_total'
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
class get_my_total:
    def GET(self, user_id):
        return r.hget("chrome_uploads_successes",user_id)

class get_phone_export:
    def GET(self, id):
        exp = session.query(PhoneExport).get(id)
        if not exp or not exp.data: return ""

class select:
    def GET(self, n):
        all = list(r.smembers("urls"))
        shuffle(all)
        return "\n".join(all[0:int(n)]) 

class add:
    def POST(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')      
        web.header('Access-Control-Allow-Headers', '*')
        web.header('Access-Control-Allow-Methods','*')
        i = web.data()
        by_name = {}
        by_email = {}           
        for record in json.loads(i):
            if len(str(record)) > 10000: 
                print "CloudspongeRecord is too big"
                continue
            owner = record.get("contacts_owner",{})
            contact = record.get("contact",{})
            user_email = record.get("user_email")
            service = record.get("service")
            first_name = re.sub('[^a-z]','',contact.get("first_name","").lower())
            last_name = re.sub('[^a-z]','',contact.get("last_name","").lower().replace('[^a-z ]',''))
            emails = contact.get("email",[{}])
            try: email_address = emails[0].get("address",'').lower()
            except: email_address = ''
            if email_address: 
                by_email.setdefault(email_address,{}).setdefault(service,[]).append(first_name + " " + last_name)
            if first_name and last_name:
                by_name.setdefault(first_name + " " + last_name,{}).setdefault(service,[]).append(email_address)            
            r = CloudspongeRecord(user_email=user_email, contacts_owner=owner, contact=contact, service=service)
            session.add(r)
        session.commit()
        return json.dumps(by_name)

class post_uploaded:
    def POST(self):
        d = json.loads(web.data())
        real_url = d.get("url")
        user_id = d.get("user_id")
        r.srem("urls", real_url)
        r.sadd("chrome_uploads",real_url)
        r.hset("chrome_uploads_users",real_url, user_id)
        return real_url

class calculate_costs:
    def POST(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')      
        web.header('Access-Control-Allow-Headers', '*')
        web.header('Access-Control-Allow-Methods','*')
        d = json.loads(web.data())
        if d.get("pw") != "9282930283029238402": 
            return None
        results = analyze(d)
        return json.dumps(results)

if __name__ == "__main__":
    app.run()

