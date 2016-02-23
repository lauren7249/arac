import hashlib
import re
import logging
import time
import sys
import os
import boto
import json
import lxml.html
from boto.s3.key import Key

from requests import session
from service import Service, S3SavedRequest
from helper import parse_out, most_common, get_center, uu
from constants import SCRAPING_API_KEY, GLOBAL_HEADERS

from geoindex.geo_point import GeoPoint
from mapquest_request import MapQuestRequest, GEOLOCATOR

def wrapper(person):
    try:
        linkedin_data = person.get("linkedin_data",{})
        location_raw = linkedin_data.get("location")
        location = GeocodeRequest(location_raw).process()
        if location:
            person["location_coordinates"] = location    
        return person
    except Exception, e:
        print __name__ + ": " + str(e)
        print json.dumps(person, indent=3)
        return person
        
class GeoCodingService(Service):

    """
    This is a two API process that takes linkedin data, finds the raw location
    and geocodes using first the Map Quest Request and second the Open Street
    Maps Request.
    """

    def __init__(self, data, *args, **kwargs):
        super(GeoCodingService, self).__init__(data, *args, **kwargs)
        self.wrapper = wrapper

class GeocodeRequest(S3SavedRequest):

    def __init__(self, location_raw):
        super(GeocodeRequest, self).__init__()
        self.logger = logging.getLogger(__name__)
        self.location_raw = location_raw

    def process(self):
        coords = {}
        if not self.location_raw:
            return coords
        self.query = "GecodeRequest" + self.location_raw
        try:
            self.key = hashlib.md5(self.query).hexdigest()
        except:
            self.key = hashlib.md5(uu(self.query)).hexdigest()
        self.boto_key = Key(self.bucket)
        self.boto_key.key = self.key   
        if self.boto_key.exists():
            html = self.boto_key.get_contents_as_string()
            coords = json.loads(html.decode("utf-8-sig"))
            if coords and coords.get("region"):
                self.logger.info('GecodeRequest: %s', 'Using S3')
                return coords    
        self.logger.info('GecodeRequest: %s', 'Calculating')       
        coords = self._get_coords()
        self.boto_key.set_contents_from_string(unicode(json.dumps(coords, ensure_ascii=False)))
        return coords        

    def _get_coords(self):
        location = {}
        if self.location_raw:
            location = MapQuestRequest(self.location_raw).process()
            if location:
                self.logger.info('MapQuest Location Found: %s', location)
                return location

            location = OpenStreetMapsRequest(self.location_raw).process()
            if location:
                self.logger.info('OpenStreetMaps Location Found: %s', location)
                return location

            #If there is a comma, try taking it out and using the
            #first chunk of the raw location as a last means effort
            first_chunk =self.location_raw.split(",")[0]
            if first_chunk != self.location_raw:
                location = MapQuestRequest(first_chunk).process()
                if location:
                    self.logger.info('Map Quest Location 2 Found: %s', location)
                    return location
        self.logger.warn("No Location")    
        return location   


class OpenStreetMapsRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via PIPL
    """

    def __init__(self, query):
        super(OpenStreetMapsRequest, self).__init__()
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.query = query

    def process(self):
        coords = {}
        if not self.query:
            return coords
        query = "OpenStreetMapsRequest" + self.query
        key = hashlib.md5(query).hexdigest()
        bucket = self.bucket
        boto_key = Key(bucket)
        boto_key.key = key   
        if boto_key.exists():
            self.logger.info('OpenStreetMapsRequest: %s', 'Using S3')
            html = boto_key.get_contents_as_string()
            coords = json.loads(html.decode("utf-8-sig"))
            return coords
        else:         
            self.logger.info('OpenStreetMapsRequest: %s', 'Querying openstreetmaps')       
            try:
                location = GEOLOCATOR.geocode(self.query)
                country = None
                locality = None
                if location and location.latitude and location.longitude:
                    try:
                        country = location.address.split(",")[-1].strip()
                        locality = ",".join(location.address.split(",")[:-1]).strip()
                    except:
                        pass
                    coords = {"latlng":(location.latitude, location.longitude), "locality":locality, "country":country}
            except:
                coords = {}
            boto_key.set_contents_from_string(unicode(json.dumps(coords, ensure_ascii=False)))
        return coords
