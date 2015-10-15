from prime.prospects.models import *
from prime.prospects.get_prospect import *
from prime.utils.networks import *
from prime.utils.bing import *
from prime.utils.geocode import *
from prime.utils import *
from geoindex.geo_point import GeoPoint
import os, json
from prime.prospects.get_prospect import company_from_url, has_common_institutions
import shutil, pandas
from consume.get_gender import *
from consume.api_consumer import *
from consume.linkedin_friend import *
import joblib

client_linkedin_id = '67910358'
client_facebook_id = 'jake.rocchi'
dir = "/Users/lauren/Documents/arachnid/p200_templates/"
base_dir = dir + client_facebook_id

leads_file = open(base_dir + "/json/leads.json", "r")
leads_str = leads_file.read()
contact_profiles = json.loads(leads_str.decode("utf-8-sig"))

leads_file = open(base_dir + "/json/extended_leads.json", "r")
leads_str = leads_file.read()
by_referrer = json.loads(leads_str.decode("utf-8-sig"))

industry_icons = pandas.read_csv('/Users/lauren/Documents/bash/industry_icons.csv', index_col='Industry').Icon.to_dict()

liscraper = LinkedinFriend()
#liscraper.login()
no_phone = 0
for ref in by_referrer.keys():
	profiles = by_referrer[ref]
	for i in xrange(0, len(profiles)):
		profile = profiles[i]
		phone = get_phone_number(profile, liscraper)				
		if phone: 
			profile["phone"] = phone
			profiles[i] = profile
		else: 
			no_phone+=1
			print profile.get("company") + " " + profile.get("website","")
		mailto = get_mailto(profile)
		if mailto:
			profile["mailto"] = mailto
			profiles[i] = profile				
	by_referrer[ref] = profiles

for i in xrange(0, len(contact_profiles)):
	profile = contact_profiles[i]
	phone = get_phone_number(profile, liscraper)				
	if phone: 
		profile["phone"] = phone
		contact_profiles[i] = profile
	else: 
		no_phone+=1
		print profile.get("company") + " " + profile.get("website","")
	mailto = get_mailto(profile)			
	if mailto: 
		profile["mailto"] = mailto
		contact_profiles[i] = profile

shutil.copyfile(dir + "common/summary.html", base_dir + "/summary.html")
shutil.copyfile(dir + "common/leads.html", base_dir + "/leads-ln.html")
shutil.copyfile(dir + "common/leads.html", base_dir + "/leads-extended.html")

extended_contact_profiles = []
for ref in by_referrer.keys():
	profiles = by_referrer[ref]
	for profile in profiles:
		extended_contact_profiles.append(profile)

extended_urls = set()
for profile in extended_contact_profiles:
	if profile.get("url") in extended_urls: 
		extended_contact_profiles.remove(profile)
		continue
	extended_urls.add(profile.get("url"))

for i in xrange(0, len(extended_contact_profiles)):
	profile = extended_contact_profiles[i]
	if profile.get("mailto"):
		emails = profile.get("mailto").split(":")[-1].split(",")
		for email in emails:
			ec = get_or_create(session, EmailContact, email=email)
			for link in ec.social_accounts: 
				domain = link.replace("https://","").replace("http://","").split("/")[0].replace("www.","").split(".")[0]
				if domain in social_domains: 
					response = requests.head(link,headers=headers)
					if response.status_code!=404:             	
						profile.update({domain:link})
	extended_contact_profiles[i] = profile

for i in xrange(0, len(extended_contact_profiles)):
	profile = extended_contact_profiles[i]
	if not profile.get("leadscore"): profile["leadscore"] = 0
	extended_contact_profiles[i] = profile

for i in xrange(0, len(extended_contact_profiles)):
	profile = extended_contact_profiles[i]
	if not profile.get("url"):
		li = from_prospect_id(profile.get("id"))
		profile["url"] = li.url
	if not profile.get("image_url"): 
		if profile.get("url").find("linkedin")>-1: 
			li = from_url(profile.get("url"))
			profile["image_url"] = li.image_url
	if not profile.get("image_url"): 
		if profile.get("facebook"): 
			fb = session.query(FacebookContact).get(profile.get("url").split('/')[-1])
			if fb:
				profile["image_url"] = fb.get_profile_info.get("image_url")
	if not profile.get("image_url"): 
		profile["image_url"] = "https://myspace.com/common/images/user.png"
	extended_contact_profiles[i] = profile

for i in xrange(0, len(extended_contact_profiles)):
	profile = extended_contact_profiles[i]
	if not profile.get("referrer_name"):
		referrer_id = profile.get("referrer_id")
		if  isinstance(referrer_id, int): 
			li = from_prospect_id(referrer_id)
			profile["referrer_name"] = li.name 
		else:
			fb = session.query(FacebookContact).get(referrer_id)
			profile["referrer_name"] = fb.get_profile_info.get("name")
	extended_contact_profiles[i] = profile

for i in xrange(0, len(extended_contact_profiles)):
	profile = extended_contact_profiles[i]
	if not profile.get("referrer_url"):
		referrer_id = profile.get("referrer_id")
		if  isinstance(referrer_id, int): 
			li = from_prospect_id(referrer_id)
			profile["referrer_url"] = li.url 
		else:
			fb = session.query(FacebookContact).get(referrer_id)
			profile["referrer_url"] = "https://www.facebook.com/" + fb.facebook_id
	extended_contact_profiles[i] = profile


extended_contact_profiles = compute_stars(extended_contact_profiles)

leads_str = unicode(json.dumps(extended_contact_profiles, ensure_ascii=False))
leads_file = open(base_dir + "/json/extended_leads_expanded.json", "w")
leads_file.write(leads_str.encode('utf8', 'replace'))
leads_file.close()

leads_str = unicode(json.dumps(contact_profiles, ensure_ascii=False))
leads_file = open(base_dir + "/json/leads.json", "w")
leads_file.write(leads_str.encode('utf8', 'replace'))
leads_file.close()

leads_str = "connectionsJ = " + unicode(json.dumps(contact_profiles, ensure_ascii=False)) + "; "
leads_file = open(base_dir + "/js/leads-ln.js", "w")
leads_file.write(leads_str.encode('utf8', 'replace'))
leads_file.close()

		
leads_str = "connectionsJ = " + unicode(json.dumps(extended_contact_profiles, ensure_ascii=False)) + "; "
leads_file = open(base_dir + "/js/leads-extended.js", "w")
leads_file.write(leads_str.encode('utf8', 'replace'))
leads_file.close()

leads_str = unicode(json.dumps(contact_profiles, ensure_ascii=False))
leads_file = open(base_dir + "/json/leads.json", "w")
leads_file.write(leads_str.encode('utf8', 'replace'))
leads_file.close()
