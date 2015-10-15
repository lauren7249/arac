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

industry_icons = pandas.read_csv('/Users/lauren/Documents/bash/industry_icons.csv', index_col='Industry').Icon.to_dict()

client_linkedin_id = '67910358'
client_facebook_id = 'jake.rocchi'
dir = "/Users/lauren/Documents/arachnid/p200_templates/"
base_dir = dir + client_facebook_id

try:
	shutil.copytree(dir + "common/img", base_dir + "/img")
	shutil.copytree(dir + "common/css", base_dir + "/css")
	shutil.copytree(dir + "common/js", base_dir + "/js")
except:
	pass

leads_file = open(base_dir + "/json/leads.json", "r")
leads_str = leads_file.read()
contact_profiles = json.loads(leads_str.decode("utf-8-sig"))

scrape = False
# fbfriend = FacebookFriend()
# # total_friends = 0
# # likers = 0
# top_engagers = {}
# for i in xrange(0, len(contact_profiles)):
# 	profile = contact_profiles[i]
# 	if profile.get("facebook"):
# 		facebook_contact = fbfriend.get_facebook_contact(profile.get("facebook"), scroll_to_bottom =True)
# 		if facebook_contact and (profile.get("image_url").find("myspace") != -1 or profile.get("image_url").find("large") != -1) and facebook_contact.get_profile_info.get("image_url"):
# 			profile["image_url"] = facebook_contact.get_profile_info.get("image_url")
# 			print facebook_contact.get_profile_info.get("image_url")
# 			contact_profiles[i] = profile
# 		if facebook_contact: 
# 			# total_friends += len(fbfriend.scrape_profile_friends(facebook_contact))
# 			# likers += len(fbfriend.get_likers(facebook_contact))
# 			top_engagers[profile.get("facebook")] = facebook_contact.top_engagers	

# for record in top_engagers:
# 	for username in record:
# 		facebook_contact = fbfriend.get_facebook_contact("http://www.facebook.com/" + username, scroll_to_bottom =True)

client_linkedin_contact = from_linkedin_id(client_linkedin_id)
client_json = client_linkedin_contact.json
linkedin_friends = set(client_json["first_degree_linkedin_ids"])
client_coords = get_mapquest_coordinates(client_linkedin_contact.location_raw).get("latlng")
client_geopoint = GeoPoint(client_coords[0],client_coords[1])

client_schools = list(set([school.name for school in client_linkedin_contact.schools]))
exclusions = [client_linkedin_contact.current_job.company.name, 'NYLIFE Securities LLC','NYLIFE Securities, LLC','NYLIFE Securities']

linkedin_friend_urls = set()

for profile in contact_profiles:
	if not profile.get("url"): 
		contact_profiles.remove(profile)
		continue

n_li = 0
n_degree = 0
n_wealth = 0
wealth_tot = 0
n_age = 0
age_tot = 0
for i in xrange(0, len(contact_profiles)):
	profile = contact_profiles[i]
	if profile.get("salary"):
		wealth_percentile = get_salary_percentile(profile.get("salary"))
		if wealth_percentile: 
			n_wealth+=1
			wealth_tot+=wealth_percentile	
			profile["wealthscore"] = wealth_percentile
	contact_profiles[i] = profile	
	if profile.get("linkedin"):
		friend_url = profile.get("linkedin")
		linkedin_friend_urls.add(friend_url)
		linkedin_contact = from_url(friend_url)
		if linkedin_contact:  
			n_li+=1
			if linkedin_contact.has_college_degree: n_degree+=1			
			if linkedin_contact.industry_raw: 
				profile["industry"] = linkedin_contact.industry_raw
				contact_profiles[i] = profile	
			# wealth_percentile = linkedin_contact.wealth_percentile()
			# if wealth_percentile: 
			# 	n_wealth+=1
			# 	wealth_tot+=wealth_percentile
			age = linkedin_contact.age
			if age:
				n_age+=1
				age_tot+=age
			name = profile.get("name")
			company = profile.get("company")
			people = linkedin_contact.json.get("people",[]) if linkedin_contact.json else []
			urls = set(bing.search_extended_network(name, school=company) + people)
			for url in urls:
				if scrape: r.sadd("urls",url)
	if not profile.get("industry") and profile.get("company"): 
		urls = bing.search_linkedin_companies(profile.get("company"))
		for url in urls:
			if scrape: r.sadd("urls",url)


by_referrer = {}
no_industry=0
for i in xrange(0, len(contact_profiles)):
	profile = contact_profiles[i]
	if not profile.get("industry") and profile.get("company"): 
		urls = bing.search_linkedin_companies(profile.get("company"))
		if not urls: continue
		company = None
		for url in urls:
			company = company_from_url(url)
			if company: break
		if not company or not company.industry: 
			print profile.get("company")
			no_industry+=1
			continue
		profile["industry"] = company.industry
		contact_profiles[i] = profile	
	if profile.get("linkedin"):
		linkedin_contact = from_url(profile.get("linkedin"))
		if linkedin_contact:  
			name = profile.get("name")
			company = profile.get("company")
			people = linkedin_contact.json.get("people",[]) if linkedin_contact.json else []
			urls = set(bing.search_extended_network(name, school=company) + people)
			profiles = []
			for url in urls:
				if url in linkedin_friend_urls: continue
				li = from_url(url)
				if not li: continue
				if str(li.linkedin_id) in linkedin_friends: continue
				if not has_common_institutions(linkedin_contact,li): continue
				valid_profile = valid_lead(li, exclude=exclusions, min_salary=35001, schools=client_schools, geopoint=client_geopoint)
				if not valid_profile: continue
				valid_profile["referrer_id"] = profile.get("id")
				valid_profile["referrer_url"] = profile.get("url")
				profiles.append(valid_profile)
			if profiles: 
				by_referrer[profile.get("id")] = profiles


all_extended_urls = set()
for ref in by_referrer.keys():
	profiles = by_referrer[ref]
	for profile in profiles:
		if not profile.get("url"): 
			profiles.remove(profile)
		elif not profile.get("referrer_url"):
			profiles.remove(profile)
		else:
			all_extended_urls.add(profile.get("url"))
	by_referrer[ref] = profiles

liscraper = LinkedinFriend()
liscraper.login()
not_3rd_degree = []
for url in all_extended_urls:
	liscraper.driver.get(url)
	degree = liscraper.wait.until(lambda driver: driver.find_element_by_xpath(".//abbr[@class='degree-icon ']"))
	if not degree or not degree.text or degree.text not in ['3rd','2nd','1st']:
		not_3rd_degree.append(url)

for url in not_3rd_degree:
	all_extended_urls.remove(url)

by_referrer = {}
final_extended_urls = set()
for i in xrange(0, len(contact_profiles)):
	profile = contact_profiles[i]
	if profile.get("linkedin"):
		linkedin_contact = from_url(profile.get("linkedin"))
		if linkedin_contact:  
			name = profile.get("name")
			company = profile.get("company")
			people = linkedin_contact.json.get("people",[]) if linkedin_contact.json else []
			urls = set(bing.search_extended_network(name, school=company) + people)
			profiles = []
			for url in urls:
				if url not in all_extended_urls: continue
				if url in linkedin_friend_urls: continue
				li = from_url(url)
				if not li: continue
				if str(li.linkedin_id) in linkedin_friends: continue
				# if url not in linkedin_contact.json.get("people",[]) and profile.get("linkedin") not in li.json.get("people",[]):
				# 	print url + "  " +  profile.get("linkedin")
				commonality = has_common_institutions(linkedin_contact,li)
				if not commonality: continue
				valid_profile = valid_lead(li, exclude=exclusions, min_salary=35001, schools=client_schools, geopoint=client_geopoint)
				if not valid_profile: continue
				final_extended_urls.add(url)
				valid_profile["referrer_id"] = profile.get("id")
				valid_profile["referrer_url"] = profile.get("url")
				valid_profile["referrer_connection"] = commonality
				valid_profile["referrer_name"] = profile.get("name")
				profiles.append(valid_profile)
			if profiles: 
				by_referrer[profile.get("id")] = profiles

company_urls = set()
no_company_url = 0
for url in list(final_extended_urls) + list(linkedin_friend_urls):
	li = from_url(url)
	if li and li.current_job:
		if li.current_job.linkedin_company:
			company_url = "https://www.linkedin.com/company/" + str(li.current_job.linkedin_company.id)
			company_urls.add(company_url)
			continue
		results = bing.search_linkedin_companies(li.current_job.company.name)
		if results: 
			company_url = results[0]
			company_urls.add(company_url)
			continue	
		no_company_url+=1	
		print li.current_job.company.name

for url in company_urls:
	r.sadd("urls",url)


industries = {}
by_industry = {}
schools = {}
by_school = {}
for i in xrange(0, len(contact_profiles)):
	profile = contact_profiles[i]
	industry = profile.get("industry")
	school = profile.get("school")
	if school:
		count = schools.get(school,0)
		schools[school] = count+1	
		profiles = by_school.get(school,[])
		profiles.append(profile)
		by_school[school] = profiles		
	if industry: 
		count = industries.get(industry,0)
		industries[industry] = count+1
		profiles = by_industry.get(industry,[])
		profiles.append(profile)
		by_industry[industry] = profiles

top_industries = sorted(industries, key=industries.get, reverse=True)[:5]

industry_info = []
for industry in top_industries:
	clean = re.sub("[^a-z]","", industry.lower())
	shutil.copyfile(dir + "common/leads.html", base_dir + "/leads-" + clean + ".html")
	if len(industry.split()) <=2: 
		label = industry
	elif industry.split()[1] in ['&','and']: 
		label = " ".join(industry.split()[:3])
	else:
		label =  " ".join(industry.split()[:2])
	d = {'clean':clean,'label':label, 'value':industries[industry], 'icon':industry_icons[industry]}
	industry_info.append(d)


school_info = []
for school in schools:
	clean = re.sub("[^a-z]","", school.lower())
	d = {'clean':clean,'label':school, 'value':schools[school]}
	school_info.append(d)


by_gender = {}
for i in xrange(0, len(contact_profiles)):
	profile = contact_profiles[i]
	name = profile.get("name")
	firstname = get_firstname(name)
	is_male = get_gender(firstname)
	if is_male is None: profile["gender"] = "Unknown"
	elif is_male: profile["gender"] = "Male"
	else: profile["gender"] = "Female"
	contact_profiles[i] = profile
	names = by_gender.get(profile["gender"],[])
	names.append(firstname)
	by_gender[profile["gender"]] = names

n_male = len(by_gender["Male"])
n_female = len(by_gender["Female"])
pct_male = float(n_male)/float(n_male+n_female)
pct_female = 1 - pct_male
percent_male = "{0:.0f}%".format(pct_male*100)
percent_female = "{0:.0f}%".format(pct_female*100)
pct_degree = float(n_degree)/float(n_li)
percent_degree = "{0:.0f}%".format(pct_degree*100)
average_age = int(float(age_tot)/float(n_age))
average_wealth = str(int(float(wealth_tot)/float(n_wealth))) + "/100"

stats = [{"name":"Male","value":percent_male},{"name":"Female","value":percent_female},{"name":"College Degree","value":percent_degree},{"name":"Average Income Score","value":average_wealth},{"name":"Average Age","value":average_age}]

vars_str = 'var colors = ["#8dd8f7", "#5bbdea", "#01a1dd", "#0079c2"]; function randColor(colors) {return colors[Math.floor(Math.random() * colors.length)]}  '
vars_str += 'var n_first_degree = ' + str(len(contact_profiles)) + ";  "
vars_str += 'industries = ' + json.dumps(industry_info) + ";  "
vars_str += 'var schools = ' + json.dumps(school_info) + ";  "
vars_str += 'var stats = ' + json.dumps(stats) + ";  "
vars_str += 'var n_extended = ' + str(len(final_extended_urls)) + ";  "
vars_str += 'var n_total = ' + str(len(final_extended_urls)+len(contact_profiles)) + ";  "
vars_str += 'client_name = ' + client_linkedin_contact.name + ";  "


vars_file = open(base_dir + "/js/vars.js", "w")
vars_file.write(vars_str)
vars_file.close()

leads_str = unicode(json.dumps(by_referrer, ensure_ascii=False))
leads_file = open(base_dir + "/json/extended_leads.json", "w")
leads_file.write(leads_str.encode('utf8', 'replace'))
leads_file.close()

leads_str = unicode(json.dumps(contact_profiles, ensure_ascii=False))
leads_file = open(base_dir + "/json/leads.json", "w")
leads_file.write(leads_str.encode('utf8', 'replace'))
leads_file.close()
# summary.html
# leads-ln.html
# extended_leads.html
# [industry].html
