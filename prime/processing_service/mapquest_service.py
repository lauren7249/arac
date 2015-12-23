import re
import logging
import sys
import os
import boto
import json
import lxml.html
from boto.s3.key import Key

from requests import session
from service import Service, S3SavedRequest
from helper import parse_out, most_common, get_center, domain_match, name_match
from constants import SCRAPING_API_KEY, GLOBAL_HEADERS

from geoindex.geo_point import GeoPoint

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR.replace("/prime", ""))
sys.path.append(BASE_DIR + "/processing_service")


class MapQuestRequest(S3SavedRequest):

    """
    Given an email address, This will return geocode JSON from mapquest
    """

    def __init__(self, query):
        super(MapQuestRequest, self).__init__()
        self.url = "https://www.mapquest.com/?q={}".format(query)
        self.query = query
        self.headers = GLOBAL_HEADERS
        self.unresolved_locations = []
        self.json_locations = []
        self.raw_search_results = None
        self.html_string = None
        self.raw_html = None
        self.lat_lng_regex = '(?<="latLng":{)[A-Za-z0-9\"\',\s\.:\-]+'
        self.countries_regex = '((?<="countryLong":\")[^\"]+(?=")|(?<="countryLong":)null)'
        self.localities_regex = '((?<="locality":\")[^\"]+(?=")|(?<="locality":)null)'
        self.regions_regex = '((?<="regionLong":\")[^\"]+(?=")|(?<="regionLong":)null)'
        self.search_results_xpath = ".//script[contains(.,'m3.dotcom.controller.MCP.addSite')]"
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def _find_location_coordinates(self):
        if not self.html_string:
            self.html_string = self._make_request()
        try:
            self.raw_html = lxml.html.fromstring(self.html_string)
            locations = self._get_json_locations()
            geocode = self._geocode_from_json()
            if not geocode:
                geocode = self._geocode_from_scraps()
            return geocode
        except Exception, e:
            self.logger.error("Location Error: %s", e)
            return None

    def _get_json_locations(self):
        if not self.html_string:
            self.html_string = self._make_request()
        if not self.raw_html:
            self.raw_html = lxml.html.fromstring(self.html_string)
        try:
            self.raw_search_results = self.raw_html.xpath(self.search_results_xpath)[0].text
            json_area = parse_out(self.raw_search_results,"m3.dotcom.controller.MCP.boot('dotcom', ","); ")
            json_data = json.loads(json_area)
            self.json_locations = json_data['model']['applications'][0]['state']['locations']
        except:
            return []
        return self.json_locations

    def _get_business_info(self,record):
        business = {}
        if not record:
            return business
        if record.get("phone"):
            business.update({"phone_number":record.get("phone")})
        if record.get("website"):
            business.update({"company_website":record.get("website")})
        if record.get("address") and isinstance(record.get("address"),dict) and record.get("address").get("singleLineAddress"):
            business.update({"company_address":record.get("address",{}).get("singleLineAddress")})
        if self._find_lat_lng(record):
            business.update({"company_latlng": self._find_lat_lng(record)})
        if record.get("inputQuery") and isinstance(record.get("inputQuery"), dict) and record.get("inputQuery").get("categories"):
            business.update({"business_categories":record.get("inputQuery",{}).get("categories")})
        return business

    def get_business(self, website=None, latlng=None, threshold_miles=75):
        unresolved = self._get_unresolved_locations()
        for record in unresolved:
            _website = record.get("website")
            _name = record.get("name")
            if _website and website and domain_match(_website, website):
                return self._get_business_info(record)
            if name_match(_name, self.query):
                if not latlng:
                    return self._get_business_info(record)
                lat, lng = self._find_lat_lng(record)
                if lat and lng:
                    _geopoint = GeoPoint(lat,lng)
                    geopoint = GeoPoint(latlng[0],latlng[1])
                    if geopoint.distance_to(_geopoint) <= threshold_miles:
                        return self._get_business_info(record)
        return {}


    def _get_unresolved_locations(self):
        if self.unresolved_locations:
            return self.unresolved_locations
        if not self.json_locations:
            self._get_json_locations()
        for location in self.json_locations:
            unresolved = location.get("unresolvedLocations")
            if unresolved:
                for u in unresolved:
                    self.unresolved_locations.append(u)
        return self.unresolved_locations

    def _geocode_from_json(self):
        coords = []
        localities = []
        regions = []
        countries = []
        for location in self.json_locations:
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

    def _find_lat_lng(self, location):
        latlng = location.get("address", {}).get("latLng", {})
        lat = latlng.get("lat")
        lng = latlng.get("lng")
        if not lat or not lng:
            return None, None
        return lat, lng

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

    def _find_scraps_locations(self):
        if not self.html_string:
            self.html_string = self._make_request()
        if not self.raw_html:
            self.raw_html = lxml.html.fromstring(self.html_string)
        if not self.raw_search_results:
            self.raw_search_results = self.raw_html.xpath(self.search_results_xpath)[0].text
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


    def process(self):
        self.logger.info('Linkedin Request: %s', 'Starting')
        self.html_string = self._make_request()
        if self.html_string:
            geocode = self._find_location_coordinates()
            return geocode
        return None
