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
from linkedin_company_service import wrapper as linkedin_company_wrapper
from bloomberg_service import BloombergRequest
from clearbit_service_webhooks import phone_wrapper as clearbit_phone_wrapper
from mapquest_request import MapQuestRequest
from person_request import PersonRequest
from helpers.stringhelpers import domestic_area, name_match, get_domain
from geoindex import GeoPoint
from geocode_service import GeocodeRequest

def wrapper(person):
    if not person:
        return person    
    try:
        current_job = PersonRequest()._current_job(person)
        if not current_job or not current_job.get("company") or name_match('Self-Employed', current_job.get("company")):
            return person  
        #enrich with linkedin company page for current job   
        person = linkedin_company_wrapper(person)
        person_coords = person.get("location_coordinates",{})
        #get person's current location, which we know we have from the leadservice
        person_latlng = person_coords.get("latlng")
        if not person_coords.get("locality"):
            person_location = person_coords.get("region")
        else:
            person_location = "{}, {}".format(person_coords.get("locality"), person_coords.get("region"))
        person_geopoint = GeoPoint(person_latlng[0], person_latlng[1])
        company_domain = get_domain(person.get("company_website"))
        #try to use closest geographic match for bloomberg
        if company_domain:
            bloomberg_request = BloombergRequest(None)
            closest_local = MapQuestRequest(current_job.get("company"), extra_info=person_location).get_closest_businesses(latlng=person_latlng, website=person.get("company_website"))
            if closest_local:
                person["phone_number"] = closest_local.get("phone_number")
                person["company_address"] = closest_local.get("company_address")
                return person            
            bloomberg_matches = bloomberg_request.pages_matching_website(company_domain)
            #find closest bloomberg match
            closest_bloomberg = bloomberg_request.closest_geo_match(bloomberg_matches, person_geopoint)
            if closest_bloomberg and closest_bloomberg.get("distance") < 75:
                person["phone_number"] = closest_bloomberg.get("phone")
                person["company_address"] = closest_bloomberg.get("company_address")         
                return person
        #try without the website constraint
        closest_local = MapQuestRequest(current_job.get("company"), extra_info=person_location).get_closest_businesses(latlng=person_latlng)
        if closest_local:
            person["phone_number"] = closest_local.get("phone_number")
            person["company_address"] = closest_local.get("company_address") 
            return person    
        bloomberg_request = BloombergRequest(None)        
        bloomberg_matches = bloomberg_request.pages_matching_name(current_job.get("company"), company_domain)
        #find closest bloomberg match
        closest_bloomberg = bloomberg_request.closest_geo_match(bloomberg_matches, person_geopoint)
        if closest_bloomberg and closest_bloomberg.get("distance") < 75:
            person["phone_number"] = closest_bloomberg.get("phone")
            person["company_address"] = closest_bloomberg.get("company_address")   
            return person   
        #if we got to this point, we will resort to clearbit
        person = clearbit_phone_wrapper(person)
        if person.get("company_address"):
            if person.get("company_address").get("lat") and person.get("company_address").get("lng"):
                geopoint = GeoPoint(person.get("company_address").get("lat"),person.get("company_address").get("lng"))
                #if the clearbit distance is too far, we wont use it
                if geopoint.distance_to(person_geopoint) > 75:
                    person["company_address"] = None
                    person["phone_number"] = None
            else:
                person["company_address"] = None
                person["phone_number"] = None
        if not person.get("company_address"):
            company_headquarters_address = person.get("company_headquarters_address")
            if company_headquarters_address and company_headquarters_address.get("stateProvince") and company_headquarters_address.get("postalCode"):
                company_headquarters_geocode = GeocodeRequest(person.get("company_headquarters")).process()
                if company_headquarters_geocode and company_headquarters_geocode.get("latlng"):
                    geopoint = GeoPoint(company_headquarters_geocode.get("latlng")[0],company_headquarters_geocode.get("latlng")[1])
                    if geopoint.distance_to(person_geopoint) < 75:
                        person["company_address"] = company_headquarters_address
    except Exception, e:
        print str(e)
    return person


class PhoneAndAddressService(Service):
    """
    Expected input is JSON with linkedin profiles
    Output is going to be existig data enriched with phone numbers
    """

    def __init__(self, data, *args, **kwargs):
        super(PhoneAndAddressService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper
        
if __name__=="__main__":
    from prime.users.models import *
    all_users = User.query.all()
    user = all_users[2]
    data = user.refresh_hiring_screen_data()
    person = data[1]

