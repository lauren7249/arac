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

client_linkedin_contact = from_linkedin_id(client_linkedin_id)
client_json = client_linkedin_contact.json
linkedin_friends = set(client_json["first_degree_linkedin_ids"])
client_facebook_contact = session.query(FacebookContact).get(client_facebook_id)
facebook_friends = set(client_facebook_contact.get_friends)
client_coords = get_mapquest_coordinates(client_linkedin_contact.location_raw).get("latlng")
client_geopoint = GeoPoint(client_coords[0],client_coords[1])

#470/508
#59 linkedin urls did not have linkedin id in html source 
#filter linkedin friends to those in the location
linkedin_contacts = []
for friend in linkedin_friends:
	contact = from_linkedin_id(friend)
	if not contact: continue
	linkedin_contacts.append(contact)

#438/811/999
#filter out facebook contacts that are definitely not local to save on api calls
facebook_contacts = []
for username in facebook_friends:
	contact = session.query(FacebookContact).get(username)
	if not contact: continue
	location = contact.get_profile_info.get("lives_in")
	if location: 
		miles = miles_apart(client_geopoint, location)
		if miles >75 or miles is None: continue
	facebook_contacts.append(contact)

#try to match by name only
#105
facebook_to_linkedin = facebook_to_linkedin_by_name(linkedin_contacts, facebook_contacts)

#315 new urls
#find possible linkedin profile urls using bing
urls_xwalk = facebook_to_bing_urls(facebook_contacts, facebook_to_linkedin)
if scrape:
	for new_urls in urls_xwalk.values():
		#scrape urls
		for url in new_urls:
			r.sadd("urls",url)

#37 matching linkedin profiles found from bing
xwalk_from_bing = facebook_to_linkedin_from_urls(facebook_contacts, urls_xwalk)
#142
facebook_to_linkedin.update(xwalk_from_bing)

#scrape new linkedin profiles for facebook contacts found by apis
#NOTE: not worth the money
if scrape:
	#296 api calls
	n_api_calls = 0
	for facebook_contact in facebook_contacts:
		if facebook_to_linkedin.get(facebook_contact.facebook_id): continue
		contact_linkedin_url = get_specific_url(facebook_contact.social_accounts, type="linkedin.com")
		n_api_calls+=1
		if contact_linkedin_url: r.sadd("urls",contact_linkedin_url)

#only 28 additional from apis
for facebook_contact in facebook_contacts:
	if facebook_to_linkedin.get(facebook_contact.facebook_id): continue
	contact_linkedin_url = get_specific_url(facebook_contact.social_accounts, type="linkedin.com")
	if not contact_linkedin_url: continue
	linkedin_contact = from_url(contact_linkedin_url)	
	if not linkedin_contact: continue
	facebook_to_linkedin[facebook_contact.facebook_id] = linkedin_contact.linkedin_id

# #NOTE: this part didnt add any value
# has_location=0
# #23 additional locations found from pipl -- none in target region
# for facebook_contact in facebook_contacts:
# 	if facebook_contact.get_location or facebook_to_linkedin.get(facebook_contact.facebook_id): 
# 		has_location+=1
# 		continue
# 	pipl = facebook_contact.get_pipl_response
# 	addresses = get_pipl_addresses(pipl)
# 	zips =  get_pipl_zips(pipl)
# 	cities =  get_pipl_cities(pipl)
# 	for address in addresses:
# 		print address
# 	for zip in zips:
# 		print zip
# 	for city in cities:
# 		print cities


# #remove linkedin proile mappings that arent in the area: 62/102 kept
# for facebook_id in facebook_to_linkedin.keys():
# 	linkedin_id = facebook_to_linkedin[facebook_id]
# 	linkedin_contact = from_linkedin_id(linkedin_id)
# 	if not linkedin_contact: 
# 		facebook_to_linkedin.pop(facebook_id,None)
# 		continue
# 	miles = miles_apart(client_geopoint, linkedin_contact.location_raw)  
# 	if miles > 75 or miles is None:
# 		print linkedin_contact.location_raw
# 		facebook_to_linkedin.pop(facebook_id,None)

# #304/348 included
# #remove facebook contacts with no linkedin and no geographic location
# excluded_facebook_contacts = []
# for facebook_contact in facebook_contacts:
# 	if facebook_contact.get_location or facebook_to_linkedin.get(facebook_contact.facebook_id): continue
# 	if facebook_contact.get_profile_info.get("job_company"): 
# 		miles = miles_apart(client_geopoint, facebook_contact.get_profile_info.get("job_company"))  
# 		if miles is None or miles>75:
# 			facebook_contacts.remove(facebook_contact)
# 			excluded_facebook_contacts.append(facebook_contact)

#438
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
	if linkedin_contact.updated< datetime.date.today(): r.sadd("urls",linkedin_contact.url)
	all_contacts.append((facebook_contact,linkedin_contact))

#798
for linkedin_contact in linkedin_contacts:
	if linkedin_contact.linkedin_id not in facebook_to_linkedin.values(): 
		if linkedin_contact.updated< datetime.date.today(): r.sadd("urls",linkedin_contact.url)
		all_contacts.append(linkedin_contact)

client_facebook_profile = client_facebook_contact.get_profile_info
client_schools = list(set([school.name for school in client_linkedin_contact.schools] + [client_facebook_profile.get("school_name")]))
exclusions = [client_facebook_profile.get("job_company"), client_linkedin_contact.current_job.company.name, 'NYLIFE Securities LLC','NYLIFE Securities, LLC','NYLIFE Securities']

#274
contact_profiles = []
n_valid=0
for contact in all_contacts:
	valid_profile = valid_lead(contact, exclude=exclusions, min_salary=35001, schools=client_schools, geopoint=client_geopoint)
	if valid_profile:
		n_valid+=1
		contact_profiles.append(valid_profile)
contact_profiles = compute_stars(contact_profiles)
leads_str = unicode(json.dumps(contact_profiles, ensure_ascii=False))

base_dir = "/Users/lauren/Documents/arachnid/p200_templates/" + client_facebook_id
try:
	os.makedirs(base_dir)
	os.makedirs(base_dir + "/json")
except: pass 
leads_file = open(base_dir + "/json/leads.json", "w")
leads_file.write(leads_str.encode('utf8', 'replace'))
leads_file.close()




