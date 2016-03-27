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

'''
--keep phone and address together as a unit
--if we know the company's website/domain, use that to filter matches, then choose:
1. closest geographic match among local pages (google places and mapquest)
2. closest geographic match for bloomberg (corporate) pages
--else:
1. closest geographic match among local pages (google places and mapquest)
2. closest geographic match for bloomberg (corporate) pages
else:
    clearbit 
'''
def wrapper(person):
    if not person:
        return person
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
    #use closest geographic match for bloomberg
    company_domain = get_domain(person.get("company_website"))
    if person.get("company_website"):
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
            person["company_address"] = closest_bloomberg.get("address")
            if not person.get("company_address"):
                person["company_address"] = person.get("company_headquarters")            
            return person
    
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
        person["company_address"] = closest_bloomberg.get("address")
        if not person.get("company_address"):
            person["company_address"] = person.get("company_headquarters")        
        return person   
    person = clearbit_phone_wrapper(person)
    if person.get("company_address"):
        company_geocode = GeocodeRequest(person.get("company_address")).process()
        if company_geocode:
            latlng = company_geocode.get("latlng")
            geopoint = GeoPoint(latlng[0],latlng[1])
            if geopoint.distance_to(person_geopoint) > 100:
                person["company_address"] = None
    if not person.get("company_address"):
        person["company_address"] = person.get("company_headquarters")
    return person


class PhoneAndAddressService(Service):
    """
    Expected input is JSON with linkedin profiles
    Output is going to be existig data enriched with phone numbers
    """

    def __init__(self, data, *args, **kwargs):
        super(PhoneService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper
        
if __name__=="__main__":
    from prime.users.models import *
    all_users = User.query.all()
    user = all_users[2]
    data = user.refresh_hiring_screen_data()
    person = data[1]

