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
from prime.prospects.models import CloudspongeRecord, PhoneExport, session, Agent, get_or_create
from services.touchpoints_costs import *
from consume.api_consumer import *
import sendgrid
import threading
from prime.utils import sendgrid_email
import requests

web.config.debug = False
urls = (
    '/select/n=(.+)', 'select',
    '/emailLinkedin/lid=(.+)', 'emailLinkedin',
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

def get_datetime(str):
    return datetime.datetime.strptime(str.split(".")[0],'%Y-%m-%d %H:%M:%S')

def get_my_ip():
    response = requests.get('https://enabledns.com/ip')
    return response.content

def url_to_s3_key(url):
	fn = url.replace("https://","").replace("http://", "").replace("/","-") + ".html"
	return fn

def get_user_failures(id):
    try:
        failures = float(r.hget("chrome_uploads_failures",id))
    except:
        failures = 0
    return failures

def get_user_successes(id):
    try:
        successes = float(r.hget("chrome_uploads_successes",id))
    except:
        successes = 0
    return successes

def get_user_success_rate(id):
    failures = get_user_failures(id)
    successes = get_user_successes(id)
    try:
        success_rate = float(successes)/float(successes+failures)   
    except:
        success_rate = 1.0
    return success_rate

def clear_user(id):
    r.hset("chrome_uploads_failures",id,0)    
    r.hset("chrome_uploads_successes",id,0)   
    r.hset("checked_out_urls",id,0)

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

class get_my_total:
    def GET(self, user_id):
        return get_user_successes(user_id)

class get_phone_export:
    def GET(self, id):
        web.header('Access-Control-Allow-Origin', '*')
        exp = session.query(PhoneExport).get(id)
        if not exp or not exp.data: return ""
        result = {}
        result['email'] = exp.sent_from
        result['export'] = exp.data
        return json.dumps(result)        

class emailLinkedin:
    def GET(self, lid):
        web.header('Content-type','text/html')
        web.header('Transfer-Encoding','chunked')
        yield "<html><body></body><head><script src='http://fgnass.github.io/spin.js/spin.min.js'></script><script>spinner = new Spinner().spin(); document.body.appendChild(spinner.el);</script></head></html>"
        try:
            url = pipl_url + "&username=" + lid + "@linkedin"
            response = requests.get(url)
            pipl_json = json.loads(response.content)   
            emails = get_pipl_emails(pipl_json)  
            yield "<script>spinner.stop()</script>"   
            yield "<script>window.open('mailto:" + emails[0] + "','_self', '');</script>"        
            #web.seeother('mailto:'+emails[0])
        except:
            yield "<script>spinner.stop()</script>"
            yield "<script>alert('Email not found')</script>"
            yield "<script>window.close()</script>"

class select:
    def GET(self, n):
        check_out_max = 2
        ip = web.ctx['ip']
        checked_out_urls = r.hget("checked_out_urls",ip)
        if checked_out_urls is None:
            r.hset("checked_out_urls",ip,0)
        checked_out_urls = int(r.hget("checked_out_urls",ip))
        if checked_out_urls>0:
            return ""
        now_time = datetime.datetime.utcnow()
        last_upload_time_str = r.hget("last_upload_time",ip)
        if last_query_time_str:
            last_upload_time = get_datetime(last_upload_time_str)
            timedelta = now_time - last_upload_time
            if timedelta.seconds <= check_out_max-1: 
                return ""        
        last_query_time_str = r.hget("last_query_time",ip)
        if last_query_time_str:
            last_query_time = get_datetime(last_query_time_str)
            timedelta = now_time - last_query_time
            if timedelta.seconds <= check_out_max: 
                return ""
        last_failure_str = r.hget("last_failure",ip)
        if last_failure_str:
            last_failure = get_datetime(last_failure_str)
            timedelta = now_time - last_failure
            if timedelta.seconds > 60*30: clear_user(ip)         
        ip_success_rate = get_user_success_rate(ip)
        ip_failures = get_user_failures(ip)
        if ip_success_rate<0.6 and ip_failures>=100:
            return ""
        all = list(r.smembers("urls"))
        shuffle(all)
        r.hset("last_query_time", ip, datetime.datetime.utcnow())
        r.hincrby("checked_out_urls",ip,check_out_max)
        return "\n".join(all[0:int(min(n,check_out_max))]) 

def email_about_contacts(user_email, client_first_name, n_contacts):
    to = user_email
    subject = client_first_name + ', Congratulations on uploading your contacts'
    body = client_first_name + ', \n\nYou uploaded ' + str(n_contacts) + " unique contacts. We are processing your data and will notify you when the analysis is complete. You should receive another email within 24 hours.\n\nThank you, \n\nThe AdvisorConnect Team"   
    sendgrid_email(to, subject, body)

class add:
    def POST(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')      
        web.header('Access-Control-Allow-Headers', '*')
        web.header('Access-Control-Allow-Methods','*')
        i = web.data()
        indata = json.loads(i)
        client_first_name = indata.get("firstName")
        user_email = indata.get("user_email")
        geolocation = indata.get("geolocation")  
        public_url = indata.get("public_url")    
        contacts_array = indata.get("contacts_array")  
        agent = get_or_create(session, Agent, email=user_email)
        agent.geolocation=geolocation
        agent.first_name=client_first_name
        agent.public_url = public_url
        session.add(agent)
        session.commit()
        by_name = {}
        by_email = {}           
        for record in contacts_array:
            if len(str(record)) > 10000: 
                print "CloudspongeRecord is too big"
                continue
            owner = record.get("contacts_owner",{})
            contact = record.get("contact",{})
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
            r = CloudspongeRecord(contacts_owner=owner, contact=contact, service=service, agent=agent)
            session.add(r)
        session.commit()
        thr = threading.Thread(target=email_about_contacts, args=(user_email,client_first_name,len(by_name)))
        thr.start() # will run "foo"   
        return json.dumps(by_name)

class post_uploaded:
    def POST(self):
        ip = web.ctx['ip']
        d = json.loads(web.data())
        real_url = d.get("url")
        user_id = d.get("user_id")
        incr = r.srem("urls", real_url)
        r.sadd("chrome_uploads",real_url)
        r.hset("chrome_uploads_users",real_url, user_id)
        r.hset("chrome_uploads_ips",real_url, ip)
        r.hincrby("checked_out_urls",ip,-1*incr)
        r.hset("last_upload_time", ip, datetime.datetime.utcnow())
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

