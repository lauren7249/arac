import web
import random
import getpass
import argparse
import datetime
import time
from random import shuffle
import json
import re
import sendgrid
import threading
from prime.utils.email import sendgrid_email
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
        user_email = indata.get("user_email")
        client_first_name = indata.get("firstName")
        f = open('data/' + user_email + '.json','w')
        f.write(json.dumps(indata)) 
        contacts_array = indata.get("contacts_array")  
        by_email = set()         
        for record in contacts_array:
            if len(str(record)) > 10000: 
                print "CloudspongeRecord is too big"
                continue
            contact = record.get("contact",{})
            emails = contact.get("email",[{}])
            try: email_address = emails[0].get("address",'').lower()
            except: email_address = ''
            if email_address: 
                by_email.add(email_address)      
        thr = threading.Thread(target=email_about_contacts, args=(user_email,client_first_name,len(by_email)))
        thr.start()        
        return json.dumps(indata)

class clearbit_webhook:
    def POST(self):
        web.header('Access-Control-Allow-Origin', '*')
        web.header('Access-Control-Allow-Credentials', 'true')      
        web.header('Access-Control-Allow-Headers', '*')
        web.header('Access-Control-Allow-Methods','*')
        signature =  web.ctx.env.get('HTTP_X_REQUEST_SIGNATURE')
        if signature != 'sha1=30005c3c712a1b1b4c47306424192130bc3081dc':
            return False
        i = json.loads(web.data())
        webhook_id = i.get("id")
        response = i.get("body")
        return True

if __name__ == "__main__":
    app.run()

