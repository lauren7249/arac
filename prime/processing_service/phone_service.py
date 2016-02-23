import logging
import hashlib
import boto
import lxml.html
import re
import dateutil
import requests
from requests import HTTPError
from boto.s3.key import Key
import multiprocessing
from service import Service, S3SavedRequest
from constants import GLOBAL_HEADERS
from linkedin_company_service import LinkedinCompanyService
from bloomberg_service import BloombergPhoneService
from clearbit_service_webhooks import ClearbitPhoneService
from mapquest_request import MapQuestRequest
from person_request import PersonRequest
from helpers.stringhelpers import domestic_area

def wrapper(person, favor_mapquest=False):
    try:
        if not person:
            return person
        if domestic_area(person.get("phone_number")) and not favor_mapquest:
            return person
        linkedin_data = person.get("linkedin_data",{})
        current_job = PersonRequest()._current_job(person)
        if not current_job or not current_job.get("company"):
            return person
        location = MapQuestRequest(linkedin_data.get("location")).process()
        latlng = location.get("latlng") if location else None
        business_service = MapQuestRequest(current_job.get("company"))
        business = business_service.get_business(latlng=latlng, website=person.get("company_website"))
        person.update(business) 
        if not domestic_area(person.get("phone_number")):
            for phone_number in person.get("pipl_phone_numbers",[]):
                if domestic_area(phone_number):
                    person["phone_number"] = phone_number
                    print "GOT PHONE FROM PIPL {}".format(phone_number)
                    break
        return person
    except Exception, e:
        print __name__ + str(e)
        return person
        
class PhoneService(Service):
    """
    Expected input is JSON with linkedin profiles
    Output is going to be existig data enriched with phone numbers
    """

    def __init__(self, data, *args, **kwargs):
        super(PhoneService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper
        
    def multiprocess(self):
        self.logstart()
        try:
            self.service = LinkedinCompanyService(self.input_data)
            self.input_data = self.service.multiprocess()        
            self.service = BloombergPhoneService(self.input_data)
            self.input_data = self.service.multiprocess()
            self.pool = multiprocessing.Pool(self.pool_size)
            self.output = self.pool.map(self.wrapper, self.input_data.get("data",[]))
            self.pool.close()
            self.pool.join()
            self.service = ClearbitPhoneService({"client_data":self.client_data,"data":self.output})
            self.output_data = self.service.multiprocess()
            #elf.output = self.user.refresh_p200_data(self.output)  
        except:
            self.logerror()
        self.logend()
        return self.output_data

