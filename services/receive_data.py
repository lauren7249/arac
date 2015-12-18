import web
import random
import getpass
import argparse
import datetime
import time
from random import shuffle

import re
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
        user_email = indata.get("user_email")
        f = open('data/' + user_email + '.json','w')
        f.write(json.dumps(indata))        
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

