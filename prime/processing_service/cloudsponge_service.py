import logging
from service import Service
from constants import EXCLUDED_EMAIL_WORDS
import re
import os
import json
from prime.prospects.models import CloudspongeRecord, get_or_create
from prime import create_app
from flask.ext.sqlalchemy import SQLAlchemy
try:
    app = create_app(os.getenv('AC_CONFIG', 'development'))
    db = SQLAlchemy(app)
    session = db.session
except Exception, e:
    print e.message
    from prime import db
    session = db.session

class CloudSpongeService(Service):

    """
    Expected input is raw JSON of cloudsponge records
    Save to database and output denormalized output by contact email

    TODO: add name resolution to improve relationship scoring
    """

    def __init__(self, client_data, data, *args, **kwargs):
        self.client_data = client_data
        self.data = data
        self.excluded_words = EXCLUDED_EMAIL_WORDS
        self.unique_emails = {}
        self.output = []
        self.session = session
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(CloudSpongeService, self).__init__(*args, **kwargs)

    def real_person(self, contact_email):
        if len(contact_email.split("@")[0])>33:
            return False
        for word in self.excluded_words: 
            if not word: continue 
            regex = '(\-|^|\.|@|^)' + word + '(\-|@|\.|$)'
            if re.search(regex,contact_email):
                return False
        return True

    def multiprocess(self):
        return self.process()

    def process(self):
        self.logger.info('Starting Process: %s', 'Cloud Sponge Service')
        try:
            for record in self.data:
                contact = record.get("contact",{})
                contact_emails = contact.get("email",[])
                if not contact_emails:
                    self.logger.warn("Contact has no email %s", unicode(json.dumps(contact, ensure_ascii=False)))
                    continue
                contact_email = contact_emails[0].get("address", "").lower()   
                owner = record.get("contacts_owner")              
                if owner:
                    account_email = owner.get("email",[{}])[0].get("address","").lower()   
                else: 
                    account_email = None    
                first_name = re.sub('[^a-z]','',contact.get("first_name","").lower())
                last_name = re.sub('[^a-z]','',contact.get("last_name","").lower().replace('[^a-z ]',''))             
                service = record.get("service","").lower()
                info = self.unique_emails.get(contact_email,{})
                sources = info.get("sources",[])
                if service.lower()=='linkedin':
                    if 'linkedin' not in sources: 
                        sources.append('linkedin')
                elif account_email and account_email not in sources:
                    sources.append(account_email)
                cs = get_or_create(self.session, CloudspongeRecord, user_email =self.client_data.get("email"), account_email=account_email, contact_email=contact_email, service=service)   
                cs.contact = contact
                cs.user_firstname = self.client_data.get("first_name")
                cs.user_lastname = self.client_data.get("last_name")
                cs.user_url = self.client_data.get("url")
                cs.user_location = self.client_data.get("location") 
                self.session.add(cs)
                if not self.real_person(contact_email):
                    self.logger.warn("Not a real person %s", contact_email)
                else:
                    job_title = contact.get("job_title")
                    companies = contact.get("companies")
                    first_name = contact.get("first_name")
                    last_name = contact.get("last_name")                          
                    self.logger.info("Person Email: %s, Job: %s, Companies: %s, Sources: %s", contact_email, job_title, companies, str(len(sources)))
                    self.unique_emails[contact_email] = {"job_title": job_title,
                                                    "companies": companies,
                                                    "first_name": first_name,
                                                    "last_name": last_name,
                                                    "sources": sources}             
            self.session.commit()           
            for key, value in self.unique_emails.iteritems():
                self.output.append({key:value})
            self.logger.info('Emails Found: %s', len(self.unique_emails))
            self.logger.info('Ending Process: %s', 'Cloud Sponge Service')  
        except:
            self.logerror()          
        return self.output
