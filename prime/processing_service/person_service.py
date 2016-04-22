import logging
import hashlib
import boto
import lxml.html
import re
import json
import dateutil
from boto.s3.key import Key
import multiprocessing
from service import Service, S3SavedRequest
from constants import GLOBAL_HEADERS
from clearbit_service_webhooks import ClearbitPersonService, person_wrapper as clearbit_wrapper
from pipl_service import PiplService, wrapper_email as pipl_wrapper
from linkedin_service_crawlera import LinkedinService, wrapper as linkedin_wrapper
from person_request import PersonRequest

def wrapper(person):
    if person.get("job_title") and person.get("companies") and person.get("first_name") and person.get("last_name"):
        full_name= "{} {}".format(person.get("first_name"),person.get("last_name")) 
        headline = "{} at {}".format(person.get("job_title",""),person.get("companies")[0])  
        linkedin_data = PersonRequest()._get_profile(headline=headline, name=full_name)   
        if linkedin_data: 
            person["linkedin_data"] = linkedin_data
            print "FOUND crawlera"
            return person 
        print "no crawlera data found for {} | {}".format(full_name, headline)    
    return EmailRequest(person).process()

class EmailRequest(S3SavedRequest):

    def __init__(self, person):
        super(EmailRequest, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.person = person

    def process(self):
        if not self.person:
            return self.person
        self.email = self.person.get("email")
        self.query = "EmailRequest" + self.email
        try:
            self.key = hashlib.md5(self.query).hexdigest()
        except:
            self.key = hashlib.md5(uu(self.query)).hexdigest()
        self.boto_key = Key(self.bucket)
        self.boto_key.key = self.key   
        if self.boto_key.exists():
            html = self.boto_key.get_contents_as_string()
            person = json.loads(html.decode("utf-8-sig"))
            if person:
                self.logger.info('EmailRequest: %s', 'Using S3')
                return person    
        self.logger.info('EmailRequest: %s', 'Calculating')     
        person = self.person  
        person = pipl_wrapper(person)
        if person.get("linkedin_url"):
            person = linkedin_wrapper(person)
            if person.get("linkedin_data"):
                print "FOUND crawlera"
                self.boto_key.set_contents_from_string(unicode(json.dumps(person, ensure_ascii=False)))
                return person    
        person = clearbit_wrapper(person)
        if person.get("linkedin_url"):
            person = linkedin_wrapper(person)
            if person.get("linkedin_data"):
                print "FOUND crawlera"
                self.boto_key.set_contents_from_string(unicode(json.dumps(person, ensure_ascii=False)))
                return person    
        self.boto_key.set_contents_from_string(unicode(json.dumps(person, ensure_ascii=False)))
        return person        

class PersonService(Service):
    """
    Expected input is JSON with emails
    Output is going to have linkedin profiles
    """

    def __init__(self, data, *args, **kwargs):
        super(PersonService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper
        self.pool_size = 20

    def _collapse(self):
        self.output = {}
        for person in self.data:
            data = person.get("linkedin_data")
            if not data:
                person["reason"] = "Not found in LinkedIn"
                person["step"] = "PersonService"
                self.excluded.append(person)                
                continue
            email = person.get("email")            
            linkedin_id = data.get("linkedin_id")
            info = self.output.get(linkedin_id,{})
            emails = info.get("email_addresses",[]) 
            emails.append(email)                 
            social_accounts = info.get("social_accounts",[]) + person.get("social_accounts",[])
            sources = info.get("sources",[]) + person.get("sources",[])
            images = info.get("images",[]) + person.get("images",[])
            output_record = {"linkedin_data": data, "email_addresses":list(set(emails)), "sources":list(set(sources)), 
                "social_accounts":list(set(social_accounts)), "images":list(set(images))}
            job_title = person.get("job_title") 
            companies = person.get("companies")
            if companies and len(companies) and companies[0] is not None:
                company = companies[0]
            else:
                company = None   
            if job_title:
                output_record["job_title"] = job_title
                output_record["company"] = company                        
            info.update(output_record)
            self.output[linkedin_id] = output_record   
        return self.output.values()
        
    def multiprocess(self):
        #UNCOMMENT TO SWITCH OFF MULTIPROCESSING
        #return self.process()
        try:
            self.logstart()
            self.pool = multiprocessing.Pool(self.pool_size)
            self.data = self.pool.map(self.wrapper, self.data)
            self.pool.close()
            self.pool.join()
            self.output = self._collapse()  
            self.logend()
        except:
            self.logerror()
        return {"data":self.output, "client_data":self.client_data, "excluded":self.excluded}                        
