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
from helper import parse_out, most_common, get_center
from constants import SCRAPING_API_KEY, GLOBAL_HEADERS

from geopy.geocoders import Nominatim
from geoindex.geo_point import GeoPoint
from mapquest_service import MapQuestRequest

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR.replace("/prime", ""))
sys.path.append(BASE_DIR + "/processing_service")

from convert import parse_html

class GeoCodingService(Service):

    """
    This is a two API process that takes linkedin data, finds the raw location
    and geocodes using first the Map Quest Request and second the Open Street
    Maps Request.
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.output = []
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        super(GeoCodingService, self).__init__(*args, **kwargs)

    def dispatch(self):
        pass

    def process(self):
        self.logger.info('Starting Process: %s', 'GeoCodingService')
        for person in self.data:
            location_raw = person.get("linkedin_data", {}).get("location")
            if location_raw:
                location = MapQuestRequest(location_raw).process()
                if location:
                    self.logger.info('MapQuest Location Found: %s', location)
                    person.update({"location_coordinates": location})
                else:
                    location = OpenStreetMapsRequest(location_raw).process()
                    if location:
                        self.logger.info('Open Street Location Found: %s', location)
                        person.update({"location_coordinates": location})
                    if not location:
                        #If there is a comma, try taking it out and using the
                        #first chunk of the raw location as a last means effort
                        first_chunk =location_raw.split(",")[0]
                        if first_chunk != location_raw:
                            location = MapQuestRequest(first_chunk).process()
                            if location:
                                self.logger.info('Map Quest Location 2 Found: %s', location)
                                person.update({"location_coordinates": location})
            else:
                self.logger.warn("No Location Found")
            self.output.append(person)
        self.logger.info('Ending Process: %s', 'GeoCodingService')
        return self.output

class OpenStreetMapsRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via PIPL
    """

    def __init__(self, query):
        self.geolocator = Nominatim()
        self.location = self.geolocator.geocode(query)
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _make_request(self):
        location = self.location
        country = None
        locality = None
        if not location or not location.latitude \
                or not location.longitude:
            return None
        try:
            country = location.address.split(",")[-1].strip()
            locality = ",".join(location.address.split(",")[:-1]).strip()
        except:
            pass
        return {"latlng":(location.latitude, location.longitude), "locality":locality, "country":country}

    def process(self):
        self.logger.info('OpenStreetMapsRequest: %s', 'Starting')
        return self._make_request()
