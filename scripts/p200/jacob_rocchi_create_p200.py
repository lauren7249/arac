from prime.prospects.models import *
from prime.prospects.get_prospect import *
from prime.utils.networks import *
from prime.utils.bing import *
from prime.utils.geocode import *
from prime.utils import *
from geoindex.geo_point import GeoPoint
import os

client_linkedin_id = '67910358'
client_facebook_id = 'jake.rocchi'

base_dir = "/Users/lauren/Documents/arachnid/p200_templates/" + client_facebook_id
try:
	os.makedirs(base_dir)
	os.makedirs(base_dir + "/json")
except: pass 

client_linkedin_contact = from_linkedin_id(client_linkedin_id)
client_json = client_linkedin_contact.json
linkedin_friends = set(client_json["first_degree_linkedin_ids"])
client_facebook_contact = session.query(FacebookContact).get(client_facebook_id)
facebook_friends = set(client_facebook_contact.get_friends)
client_coords = get_mapquest_coordinates(client_linkedin_contact.location_raw).get("latlng")
client_geopoint = GeoPoint(client_coords[0],client_coords[1])

#182/469/508
#59 linkedin urls did not have linkedin id in html source 
#filter linkedin friends to those in the location
linkedin_contacts = []
for friend in linkedin_friends:
	contact = from_linkedin_id(friend)
	if not contact: continue
	mapquest = get_mapquest_coordinates(contact.location_raw)
	if mapquest:
		coords = mapquest.get("latlng")
		if coords:
			geopoint = GeoPoint(coords[0],coords[1])
			miles_apart = client_geopoint.distance_to(geopoint)    
			if miles_apart > 75:
				print contact.location_raw
				continue
	linkedin_contacts.append(contact)

#348/811/999
#filter facebook contacts to those not necessarily out of the location
facebook_contacts = []
for username in facebook_friends:
	contact = session.query(FacebookContact).get(username)
	if not contact: continue
	location = contact.get_location
	if location:
		mapquest = get_mapquest_coordinates(location)
		if mapquest:
			coords = mapquest.get("latlng")
			if coords:
				geopoint = GeoPoint(coords[0],coords[1])
				miles_apart = client_geopoint.distance_to(geopoint)    
				if miles_apart > 75:
					print contact.get_location
					continue	
	facebook_contacts.append(contact)

names = {}
for linkedin_contact in linkedin_contacts:
	linkedin_name = linkedin_contact.name.lower()
	for word in linkedin_name.split(" "):
		cts = names.get(word, [])
		cts.append(linkedin_contact)
		names[word] = cts

from difflib import SequenceMatcher
def name_match(name1, name2):
	name1 = name1.lower()
	name2 = name2.lower()
	name1_words = set(name1.split(" "))
	name2_words = set(name2.split(" "))
	intersect = name1_words & name2_words
	if len(intersect)>=2: return True
	ratio = SequenceMatcher(None, name1, name2)
	if ratio>=0.8: return True
	return False

#try to match by name only
#45
facebook_to_linkedin = {}
for facebook_contact in facebook_contacts:
	linkedin_match = False
	profile_info = facebook_contact.get_profile_info
	facebook_name = profile_info.get("name").lower() if profile_info and profile_info.get("name") else ""
	facebook_words = set(facebook_name.split(" "))
	matching_linkedin_contacts = []
	for word in facebook_words:	
		for linkedin_contact in names.get(word, []):
			matching_linkedin_contacts.append(linkedin_contact)
	for linkedin_contact in matching_linkedin_contacts:
		linkedin_name = linkedin_contact.name.lower()
		intersect = facebook_words & set(linkedin_name.split(" "))
		if len(intersect)>=2: 
			print facebook_name + " == " + linkedin_name		
			facebook_to_linkedin[facebook_contact.facebook_id] = linkedin_contact.linkedin_id
			linkedin_match = True
			break

#scrape new linkedin profiles for facebook contacts found by apis
for facebook_contact in facebook_contacts:
	if facebook_to_linkedin.get(facebook_contact.facebook_id): continue
	contact_linkedin_url = get_specific_url(facebook_contact.social_accounts, type="linkedin.com")
	if contact_linkedin_url: r.sadd("urls",contact_linkedin_url)

#only 31 additional from apis
for facebook_contact in facebook_contacts:
	if facebook_to_linkedin.get(facebook_contact.facebook_id): continue
	contact_linkedin_url = get_specific_url(facebook_contact.social_accounts, type="linkedin.com")
	if not contact_linkedin_url: continue
	linkedin_contact = from_url(contact_linkedin_url)	
	if not linkedin_contact: continue
	facebook_to_linkedin[facebook_contact.facebook_id] = linkedin_contact.linkedin_id

#NOTE: this part didnt add any value
has_location=0
#23 additional locations found from pipl -- none in target region
for facebook_contact in facebook_contacts:
	if facebook_contact.get_location or facebook_to_linkedin.get(facebook_contact.facebook_id): 
		has_location+=1
		continue
	pipl = facebook_contact.get_pipl_response
	addresses = get_pipl_addresses(pipl)
	zips =  get_pipl_zips(pipl)
	cities =  get_pipl_cities(pipl)
	for address in addresses:
		print address
	for zip in zips:
		print zip
	for city in cities:
		print cities

#168 new urls
#find possible linkedin profile urls using bing
new_urls = set()
for facebook_contact in facebook_contacts:
	if facebook_contact.get_location or facebook_to_linkedin.get(facebook_contact.facebook_id): continue
	name = facebook_contact.get_profile_info.get("name")
	job_title = facebook_contact.get_profile_info.get("job_title") 
	if job_title in ["Works","Worked"]: job_title = None
	job_company = facebook_contact.get_profile_info.get("job_company")
	school_name = facebook_contact.get_profile_info.get("school_name")
	school_major = facebook_contact.get_profile_info.get("school_major")
	if job_company: 
		urls = bing.search_linkedin_by_name(name, school=job_company, page_limit=22, limit=1000)
		new_urls.update(urls)
	if job_title: 
		urls = bing.search_linkedin_by_name(name, school=job_title, page_limit=22, limit=1000)
		new_urls.update(urls)
	if school_major: 
		urls = bing.search_linkedin_by_name(name, school=school_major, page_limit=22, limit=1000)
		new_urls.update(urls)
	if school_name: 
		urls = bing.search_linkedin_by_name(name, school=school_name, page_limit=22, limit=1000)
		new_urls.update(urls)
#scrape urls
for url in new_urls:
	r.sadd("urls",url)

#17 matching linkedin profiles found from bing
for facebook_contact in facebook_contacts:
	if facebook_contact.get_location or facebook_to_linkedin.get(facebook_contact.facebook_id): continue
	name = facebook_contact.get_profile_info.get("name")
	job_title = facebook_contact.get_profile_info.get("job_title") 
	if job_title in ["Works","Worked"]: job_title = None
	job_company = facebook_contact.get_profile_info.get("job_company")
	school_name = facebook_contact.get_profile_info.get("school_name")
	school_major = facebook_contact.get_profile_info.get("school_major")
	found_match = False
	if job_company: 
		urls = bing.search_linkedin_by_name(name, school=job_company, page_limit=22, limit=1000)
		for url in urls:
			li = from_url(url)
			if not li: continue
			for job in li.jobs:
				if not job.company or not job.company.name: continue
				if name_match(job_company, job.company.name):
					print job_company + "-->" + job.company.name
					facebook_to_linkedin[facebook_contact.facebook_id] = li.linkedin_id
					found_match = True
					break
			if found_match: break
	if found_match: continue
	if job_title: 
		urls = bing.search_linkedin_by_name(name, school=job_title, page_limit=22, limit=1000)
		for url in urls:
			li = from_url(url)
			if not li: continue
			for job in li.jobs:
				if not job.title: continue
				if name_match(job_title, job.title):
					print job_title + "-->" + job.title
					facebook_to_linkedin[facebook_contact.facebook_id] = li.linkedin_id
					found_match = True
					break
			if found_match: break
	if found_match: continue
	if school_major: 
		urls = bing.search_linkedin_by_name(name, school=school_major, page_limit=22, limit=1000)
		for url in urls:
			li = from_url(url)
			if not li: continue
			for school in li.schools:
				if not school.degree: continue
				if name_match(school.degree, school_major):
					print school_major + "-->" + school.degree
					facebook_to_linkedin[facebook_contact.facebook_id] = li.linkedin_id
					found_match = True
					break
			if found_match: break
	if found_match: continue
	if school_name: 
		urls = bing.search_linkedin_by_name(name, school=school_name, page_limit=22, limit=1000)
		for url in urls:
			li = from_url(url)
			if not li: continue
			for school in li.schools:
				if not school.name: continue
				if name_match(school.name, school_name):
					print school_name + "-->" + school.name
					facebook_to_linkedin[facebook_contact.facebook_id] = li.linkedin_id
					found_match = True
					break
			if found_match: break

#remove linkedin proiles that arent in the area: 62/100 kept
for facebook_id in facebook_to_linkedin.keys():
	linkedin_id = facebook_to_linkedin[facebook_id]
	linkedin_contact = from_linkedin_id(linkedin_id)
	if not linkedin_contact: 
		facebook_to_linkedin.pop(facebook_id,None)
		continue
	mapquest = get_mapquest_coordinates(linkedin_contact.location_raw)
	if not mapquest:
		facebook_to_linkedin.pop(facebook_id,None)
		continue		
	coords = mapquest.get("latlng")
	if not coords:
		facebook_to_linkedin.pop(facebook_id,None)
		continue			
	geopoint = GeoPoint(coords[0],coords[1])
	miles_apart = client_geopoint.distance_to(geopoint)    
	if miles_apart > 75:
		print linkedin_contact.location_raw
		facebook_to_linkedin.pop(facebook_id,None)
		continue	

#240/348 included
#remove facebook contacts with no linkedin and no geographic location
excluded_facebook_contacts = []
for facebook_contact in facebook_contacts:
	if facebook_contact.get_location or facebook_to_linkedin.get(facebook_contact.facebook_id): continue
	if facebook_contact.get_profile_info.get("job_company"): 
		coords = get_mapquest_coordinates(facebook_contact.get_profile_info.get("job_company"))
		latlng = coords.get("latlng")
		if latlng and coords.get("locality"):
			geopoint = GeoPoint(latlng[0],latlng[1])
			miles_apart = client_geopoint.distance_to(geopoint)    
			if miles_apart <= 75:
				continue
	facebook_contacts.remove(facebook_contact)
	excluded_facebook_contacts.append(facebook_contact)

#240
all_contacts = []
for facebook_contact in facebook_contacts:
	linkedin_id = facebook_to_linkedin.get(facebook_contact.facebook_id)
	if not linkedin_id: 
		all_contacts.append(facebook_contact)
		continue
	linkedin_contact = from_linkedin_id(linkedin_id)
	if not linkedin_contact:
		all_contacts.append(facebook_contact)
		continue	
	all_contacts.append((facebook_contact,linkedin_contact))

#385
for linkedin_contact in linkedin_contacts:
	if linkedin_contact.linkedin_id not in facebook_to_linkedin.values(): all_contacts.append(linkedin_contact)

client_facebook_profile = client_facebook_contact.get_profile_info
client_schools = list(set([school.name for school in client_linkedin_contact.schools] + [client_facebook_profile.get("school_name")]))
exclusions = [client_facebook_profile.get("job_company"), client_linkedin_contact.current_job.company.name, 'NYLIFE Securities LLC','NYLIFE Securities, LLC','NYLIFE Securities']
contact_profiles = []
n_valid=0
for contact in all_contacts:
	valid_profile = valid_lead(contact, exclude=exclusions, min_salary=35001, schools=client_schools)
	if valid_profile:
		n_valid+=1
		contact_profiles.append(valid_profile)
contact_profiles = compute_stars(contact_profiles)
for profile in contact_profiles:
	if re.search("Intern(,|\s|$)",profile.get("job")): contact_profiles.remove(profile)
leads_str = unicode(json.dumps(contact_profiles, ensure_ascii=False))
leads_file = open(base_dir + "/json/leads.json", "w")
leads_file.write(leads_str)
leads_file.close()




