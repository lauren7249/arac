import requests
from . import headers
import lxml.html
from geoindex.geo_point import GeoPoint
# import reverse_geocoder as rg
from consume.convert import uu
import re
import numpy as np
import itertools
import operator
from prime.prospects.models import session
from consume.linkedin_friend import LinkedinFriend
import time
from geopy.geocoders import Nominatim
import json

def parse_out(text, startTag, endTag):
	region = ""
	region_start = text.find(startTag)
	if region_start > -1:
		region = text[region_start+len(startTag):]
		region_end = region.find(endTag)
		if region_end > -1:
			region = region[:region_end]	
	return region

def add_lat_long(text, location):
	region_start = text.find('"lng":')
	text = text[region_start+6:]

	region = parse_out(text, '"lat":', ',')
	if len(region): location["lat"] = region	

	region = parse_out(text, '"lng":', '}')
	if len(region): location["lng"] = region	

	if location["lat"] == "null":
		location = add_lat_long(text, location)
	return location

def most_common(L):
  # get an iterable of (item, iterable) pairs
	SL = sorted((x, i) for i, x in enumerate(L))
  # print 'SL:', SL
  	groups = itertools.groupby(SL, key=operator.itemgetter(0))
  # auxiliary function to get "quality" for an item
	def _auxfun(g):
		item, iterable = g
		count = 0
		min_index = len(L)
		for _, where in iterable:
			count += 1
			min_index = min(min_index, where)
	    # print 'item %r, count %r, minind %r' % (item, count, min_index)
		return count, -min_index
	  # pick the highest-count/earliest item
	try:
		return max(groups, key=_auxfun)[0]
	except:
		return None

def get_google_results(liscraper, query):
	from prime.prospects.models import session, GoogleMapsSearch
	if not query: return None
	query = query.strip().replace(" ","+")
	rec = session.query(GoogleMapsSearch).get(query)
	if rec: return rec
	rec = GoogleMapsSearch(query=query)
	url = "https://www.google.com/maps/search/" + query
	if liscraper:
		if not liscraper.is_logged_in: liscraper.login()
		try:
			liscraper.driver.get(url)
		except:
			try:
				liscraper = LinkedinFriend()
				liscraper.driver.get(url)
				source = liscraper.driver.page_source
			except:
				return None
	else:
		time.sleep(1)
		response = requests.get(url, headers=headers)
		if response.status_code != 200: 
			print "google blocked us!!!"
			return None
		source = response.content

	phone_numbers = re.findall('\([0-9]{3}\) [0-9]{3}\-[0-9]{4}',source)
	google_links = re.findall('https://plus.google.com/[0-9A-Za-z]+/',source)
	rec.phone_numbers = phone_numbers
	rec.plus_links = google_links
	session.add(rec)
	session.commit()
	return rec

def search_openstreetmaps(raw):
	if not raw:
		return None
	geolocator = Nominatim()
	location = geolocator.geocode(raw)
	if not location or not location.latitude or not location.longitude or not location.address:
		return None
	country = location.address.split(",")[-1].strip()
	locality = ",".join(location.address.split(",")[:-1]).strip()
	return {"latlng":(location.latitude, location.longitude), "locality":locality, "country":country}

def search_mapquest_coordinates(raw):
	if not raw: 
		return None
	url =  "https://www.mapquest.com/?q=%s" % (raw)
	try:
		response = requests.get(url, headers=headers)
		raw_html = lxml.html.fromstring(response.content)
		raw_search_results = raw_html.xpath(".//script[contains(.,'m3.dotcom.controller.MCP.addSite')]")[0].text
	except:
		return search_openstreetmaps(raw)
	json_area = parse_out(raw_search_results,"m3.dotcom.controller.MCP.boot('dotcom', ","); ")
	try:
		json_data = json.loads(json_area)
		locations = json_data['model']['applications'][0]['state']['locations']
		return geocode_from_json(locations)
	except:
		return geocode_from_scraps(response.content)

def geocode_from_json(locations):
	coords = []
	localities = []
	regions = []
	countries = []
	for location in locations:
		address = location.get("address")
		if not address:
			continue
		latlng = address.get("latLng")
		if not latlng:
			continue
		lat = latlng.get("lat")
		lng = latlng.get("lng")
		if not lat or not lng: 
			continue
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
		# , "latlng_result":rg.get((center.latitude, center.longitude)) if center else None
		}
		return geocode
	return search_openstreetmaps(raw)	

def geocode_from_scraps(raw_search_results):
	latlng = re.findall('(?<="latLng":{)[A-Za-z0-9\"\',\s\.:\-]+', raw_search_results)
	if len(latlng) < 2 : 
		return search_openstreetmaps(raw)
	latlng = latlng[0:len(latlng)-1]
	countries = re.findall('((?<="countryLong":\")[^\"]+(?=")|(?<="countryLong":)null)', raw_search_results)
	if len(countries) < 2: 
		return search_openstreetmaps(raw)
	countries = countries[0:len(countries)-1]		
	localities = re.findall('((?<="locality":\")[^\"]+(?=")|(?<="locality":)null)', raw_search_results)
	if len(localities) >=2: 
		localities = localities[0:len(localities)-1]
	else:
		localities = []
	regions = re.findall('((?<="regionLong":\")[^\"]+(?=")|(?<="regionLong":)null)', raw_search_results)
	if len(regions)>=2: 
		regions = regions[0:len(regions)-1]
	main_locality = most_common(localities)
	main_region = most_common(regions)
	main_country = most_common(countries)
	if main_locality =='null': main_locality=None
	if main_region=='null': main_region=None
	if main_country=='null': main_country=None
	coords = []
	for result in latlng:
		current = [float(x) for x in re.findall('[0-9\.\-]+',result)]
		if len(current)==2: coords.append(GeoPoint(current[0],current[1]))
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
	if uu(raw.split(",")[0]) != uu(raw):
		return search_mapquest_coordinates(raw.split(",")[0])
	return search_openstreetmaps(raw)	

#a relic 
def get_mapquest_coordinates(raw):
	from prime.prospects.models import MapquestGeocodes
	return MapquestGeocodes.get_coordinates(raw, use_db=True)

def get_center(coords, remove_outliers=False):
	distances = []
	for coord in coords:
		total_distance = 0
		for coord2 in coords:
			total_distance += coord.distance_to(coord2)
		distances.append(total_distance)
	if remove_outliers:
		for i in xrange(len(coords)):
			if distances[i] > np.mean(distances) + np.std(distances): coords.remove(coords[i])
	min_total_distance = None
	center = None
	for coord in coords:
		total_distance = 0
		for coord2 in coords:
			total_distance += coord.distance_to(coord2)		
		if total_distance<min_total_distance or min_total_distance is None: 
			min_total_distance = total_distance
			center = coord	
	return center

def get_mapquest(raw):
	location = {}
	url =  "https://www.mapquest.com/?q=%s" % (raw)
	try:
		response = requests.get(url, headers=headers)
		response_text = response.content

		region = parse_out(response_text, '"countryLong":"', '","')
		if len(region): location["country"] = region	

		region = parse_out(response_text, '"region":"', '","')
		if len(region): location["region"] = region

		region = parse_out(response_text, '"locality":"', '","')
		if len(region): location["locality"] = region

		location = add_lat_long(response_text, location)
	except:
		pass
	return location

def location_string(location):
	if location is None or len(location)==0: return None
	if location.get("locality") is None:
		if location.get("region") is None:
			return location.get("country")
		else:
			return location.get("region") + ", " + location.get("country")
	else:
		if location.get("region") is None:
			return location.get("locality") + ", " + location.get("country")
		else:
			return location.get("locality") + ", " + location.get("region") + ", " + location.get("country")

def geocode(raw):
	location = get_mapquest(raw)
	return location_string(location), location

def miles_apart(point, location_string):
	mapquest = get_mapquest_coordinates(location_string)
	if not mapquest: return None
	coords = mapquest.get("latlng")
	if not coords: return None
	geopoint = GeoPoint(coords[0],coords[1])
	miles_apart = geopoint.distance_to(point)    
	return miles_apart
