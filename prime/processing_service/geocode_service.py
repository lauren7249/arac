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

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR.replace("/prime", ""))
sys.path.append(BASE_DIR + "/processing_service")

from consume.convert import parse_html

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


class MapQuestRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via PIPL
    """
    #TODO implement geocode from scraps

    def __init__(self, query):
        self.url = "https://www.mapquest.com/?q={}".format(query)
        self.query = query
        self.headers = GLOBAL_HEADERS
        self.raw_search_results = None
        self.lat_lng_regex = '(?<="latLng":{)[A-Za-z0-9\"\',\s\.:\-]+'
        self.countries_regex = '((?<="countryLong":\")[^\"]+(?=")|(?<="countryLong":)null)'
        self.localities_regex = '((?<="locality":\")[^\"]+(?=")|(?<="locality":)null)'
        self.regions_regex = '((?<="regionLong":\")[^\"]+(?=")|(?<="regionLong":)null)'
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _find_lat_lng(self, location):
        latlng = location.get("address", {}).get("latLng", {})
        lat = latlng.get("lat")
        lng = latlng.get("lng")
        if not lat or not lng:
            return None, None
        return lat, lng

    def _geocode_from_json(self, locations):
        coords = []
        localities = []
        regions = []
        countries = []
        for location in locations:
            address = location.get("address")
            lat, lng = self._find_lat_lng(location)
            if lat and lng:
                coords.append(GeoPoint(lat,lng))
                regions.append(address.get("regionLong"))
                localities.append(address.get("locality"))
                countries.append(address.get("countryLong"))
        main_locality = most_common(localities)
        main_region = most_common(regions)
        main_country = most_common(countries)
        if main_locality =='null': main_locality=None
        if main_region=='null': main_region=None
        if main_country=='null': main_country=None
        locality_coords = []
        for i in xrange(len(coords)):
            if localities[i] == main_locality and regions[i] == main_region and countries[i]==main_country:
                locality_coords.append(coords[i])
        center = get_center(locality_coords)
        if center:
            geocode = {"latlng":(center.latitude, center.longitude), "locality":main_locality, "region":main_region,"country":main_country
                    }
            return geocode
        return {}

    def _find_scraps_locations(self):
        latlng = re.findall(self.lat_lng_regex, self.raw_search_results)
        countries = re.findall(self.countries_regex, self.raw_search_results)
        localities = re.findall(self.localities_regex, self.raw_search_results)
        regions = re.findall(self.regions_regex, self.raw_search_results)
        if len(latlng) < 2 :
            return [], [], [], []
        latlng = latlng[0:len(latlng)-1]
        if len(countries) < 2:
            return [], [], [], []
        countries = countries[0:len(countries)-1]
        if len(localities) >=2:
            localities = localities[0:len(localities)-1]
        else:
            localities = []
        if len(regions)>=2:
            regions = regions[0:len(regions)-1]
        return latlng, countries, localities, regions

    def _geocode_from_scraps(self):
        latlng, countries, localities, regions = self._find_scraps_locations()
        main_locality = most_common(localities)
        main_region = most_common(regions)
        main_country = most_common(countries)
        if main_locality =='null': main_locality=None
        if main_region=='null': main_region=None
        if main_country=='null': main_country=None
        coords = []
        for result in latlng:
            current = [float(x) for x in re.findall('[0-9\.\-]+',result)]
            if len(current)==2:
                coords.append(GeoPoint(current[0],current[1]))
        locality_coords = []
        if len(coords) == len(localities) and len(coords) == len(countries) and len(regions)==len(coords) and main_locality:
            for i in xrange(len(coords)):
                if localities[i] == main_locality and regions[i] == main_region and countries[i]==main_country:
                    locality_coords.append(coords[i])
                center = get_center(locality_coords)
        else:
            center = get_center(coords)
        if center:
            geocode = {"latlng":(center.latitude, center.longitude), "locality":main_locality, "region":main_region,"country":main_country
                    # , "latlng_result":rg.get((center.latitude, center.longitude)) if center else None
                    }
            return geocode
        return None


    def _find_location_coordinates(self, html):
        try:
            raw_html = lxml.html.fromstring(html)
            self.raw_search_results = raw_html.xpath(".//script[contains(.,'m3.dotcom.controller.MCP.addSite')]")[0].text
            json_area = parse_out(self.raw_search_results,"m3.dotcom.controller.MCP.boot('dotcom', ","); ")
            json_data = json.loads(json_area)
            locations = json_data['model']['applications'][0]['state']['locations']
            geocode = self._geocode_from_json(locations)
            if not geocode:
                geocode = self._geocode_from_scraps()
            return geocode
        except Exception, e:
            self.logger.error("Location Error: %s", e)
            return None

    def process(self):
        self.logger.info('Linkedin Request: %s', 'Starting')
        html = self._make_request()
        if html:
            geocode = self._find_location_coordinates(html)
            return geocode
        return None


class OpenStreetMapsRequest(S3SavedRequest):

    """
    Given an email address, This will return social profiles via PIPL
    """

    def __init__(self, query):
        self.geolocator = Nominatim()
        self.location = geolocator.geocode(query)
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
        self.logger.info('Linkedin Request: %s', 'Starting')
        return self._make_request()
