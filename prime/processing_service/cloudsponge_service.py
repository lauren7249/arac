import logging
from service import Service
from constants import EXCLUDED_EMAIL_WORDS
import re
import os
import json

class CloudSpongeService(Service):

    """
    Input 
            {"data":[{raw cloudsponge}]}
    Output 
            {"data":[{processed cloudsponge}]} unique by email 
    TODO: add name resolution to improve relationship scoring
    """

    def __init__(self, data, *args, **kwargs):
        super(CloudSpongeService, self).__init__(data, *args, **kwargs)
        self.excluded_words = EXCLUDED_EMAIL_WORDS
        self.unique_people = {}

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
        self.logstart()
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
                service = record.get("service","").lower()

                if contact_email:
                    key = contact_email
                elif service=="linkedin":
                    key = str(contact.values())
                if not key:
                    continue                     

                first_name = re.sub('[^a-z]','',contact.get("first_name","").lower())
                last_name = re.sub('[^a-z]','',contact.get("last_name","").lower().replace('[^a-z ]',''))             
                info = self.unique_people.get(key,{})
                sources = info.get("sources",[])
                if service.lower()=='linkedin':
                    if 'linkedin' not in sources: 
                        sources.append('linkedin')
                elif account_email and account_email not in sources:
                    sources.append(account_email)

                job_title = contact.get("job_title")
                companies = contact.get("companies")
                first_name = contact.get("first_name")
                last_name = contact.get("last_name")                          
                #self.logger.info("Person Email: %s, Job: %s, Companies: %s, Sources: %s", contact_email, job_title, companies, str(len(sources)))
                self.unique_people[key] = {"job_title": job_title,
                                                "companies": companies,
                                                "first_name": first_name,
                                                "last_name": last_name,
                                                "sources": sources,
                                                "email": contact_email}                      
            for key, info in self.unique_people.iteritems():
                email = info.get("email")
                if 'linkedin' not in info.get("sources") and not self.real_person(email):
                    self.logger.warn("Not a real person %s", email)
                    self.excluded.append({"email":email, "sources":sources, "reason":"Email address did not identify a real person","step":"CloudSpongeService"})
                    continue              
                info["email"] = email
                self.output.append(info)
            self.logend()
        except:
            self.logerror()          
        return {"data":self.output, "client_data":self.client_data, "excluded":self.excluded}
