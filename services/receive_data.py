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
from prime.prospects.models import PhoneExport, session, get_or_create
from prime.prospects.lead_model import CloudspongeRecord
from prime.prospects.agent_model import Agent
from services.touchpoints_costs import *
from consume.api_consumer import *
import sendgrid
import threading
from prime.utils import sendgrid_email
import requests
import sys

web.config.debug = False
urls = (
    '/add', 'add',
    '/clearbit_webhook', 'clearbit_webhook'
)

app = web.application(urls, globals())
web_session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})

def email_about_contacts(user_email, client_first_name, n_contacts):
    to = user_email
    subject = client_first_name + ', Congratulations on uploading your contacts'
    body = client_first_name + ', \n\nYou uploaded ' + str(n_contacts) + " unique contacts. We are processing your data and will notify you when the analysis is complete. \n\nThank you, \n\nThe AdvisorConnect Team"   
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
        try:
            session.add(agent)
            session.commit()
        except:
            session.rollback()
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
            cs = CloudspongeRecord(contacts_owner=owner, contact=contact, service=service, agent=agent)
            session.add(cs)
        session.commit()
        thr = threading.Thread(target=email_about_contacts, args=(user_email,client_first_name,len(by_name)))
        thr.start() # will run "foo"   
        return json.dumps(by_name)

class clearbit_webhook:
    def POST(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')      
        web.header('Access-Control-Allow-Headers', '*')
        web.header('Access-Control-Allow-Methods','*')
        print web.ctx.env
        i = json.loads(web.data())
        webhook_id = i.get("id")
        response = i.get("body")
        r.hset("clearbit_webhooks",webhook_id,json.dumps(response))
        return "true"


if __name__ == "__main__":
    app.run()

