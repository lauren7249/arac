from prime.prospects.models import *
from prime.prospects.get_prospect import *
from prime.utils.bing import *
from prime.utils.geocode import *
import scipy.stats as stats
import datetime
import joblib
import re

# pegasos_model = joblib.load("../data/pegasos_model.dump")

# def title_qualifies(title):
# 	try:
# 		title_split = re.sub('[^A-Za-z0-9]+', ' ', title).lower().split()
# 	except:
# 		print "error"
# 		return False
# 	d = dict((i,title_split.count(i)) for i in title_split)
# 	dotproduct=0
# 	for j in d:
# 		if j in pegasos_model: dotproduct+=d[j]*pegasos_model[j] 
# 	return (dotproduct > 0)

def agent_network(prospects, locales=['New York','Greater New York City Area']):
	#employed, in ny, not in financial services
	new_york_employed = []
	for prospect in prospects:
		if valid_lead(prospect, locales=locales): new_york_employed.append(prospect)  
	return new_york_employed

def valid_lead(lead, locales=None, exclude=[], schools=[],min_salary=60000, geopoint=None):
	prospect_schools = None
	if not lead: return False
	if isinstance(lead, Prospect):
		prospect = lead
		location = prospect.get_location
		if not location: 
			print "no location"
			return False				
		if locales and location.split(", ")[-1] not in locales:
			print location + " not local" 
			return False
		if geopoint:
			miles = miles_apart(geopoint, location)
			if miles>75 or miles is None: 
				print location + " not local" 	
				return False		
		if prospect.current_job is None or (prospect.current_job.end_date and prospect.current_job.end_date < datetime.date.today()): 
			print "no job " + prospect.url
			return False
		if prospect.current_job.company.name in exclude: 
			print prospect.current_job.company.name + " at the same company " 
			return False
		if prospect.current_job.title and re.search("Intern(,|\s|$)",prospect.current_job.title):
			print prospect.current_job.title + " not a real job"
			return False
		salary = prospect.get_max_salary
		if salary>0 and salary < min_salary and (prospect.current_job.start_date and (datetime.date.today() - prospect.current_job.start_date).days < 365*3): 
			print str(salary) + " too low for " + prospect.current_job.title 
			return False	
		profile = clean_profile(prospect.build_profile)	
		profile["location"] = location
		if salary>0: profile["salary"] = salary
		prospect_schools = [school.name for school in prospect.schools]
		social_accounts = prospect.social_accounts
	elif isinstance(lead, FacebookContact):
		contact = lead
		profile_info = contact.get_profile_info
		if not profile_info:
			print "no profile info for " + contact.facebook_id
		location = contact.get_location
		if not location: 
			print "no location"
			return False		
		if locales and location.split(", ")[-1] not in locales:
			print location + " not local"
			return False
		if geopoint:
			miles = miles_apart(geopoint, location)
			if miles>75 or miles is None: 
				print location + " not local" 		
				return False					
		if profile_info.get("job_company") and profile_info.get("job_company").split(",")[0] in exclude :
			print profile_info.get("job_company") + " at the same company"
			return False
		if profile_info.get("job_title") and (re.search("Intern(,|\s|$)",profile_info.get("job_title")) or profile_info.get("job_title").find("Former") == 0 or profile_info.get("job_title")=='Worked'):
			print profile_info.get("job_title") + " not a real job"
			return False
		salary = contact.get_max_salary 
		if salary<0 and not profile_info.get("job_title"):
			print "no job " + profile_info.get("job_title"," ") + " " + profile_info.get("job_company"," ")
			return False
		if salary>0 and salary < min_salary and profile_info.get("job_title") != "Works":
			print str(salary) + " too low for " + profile_info.get("job_title")
			return False
		profile = clean_profile(contact.build_profile)
		profile["location"] = location
		if salary>0: profile["salary"] = salary
		social_accounts = contact.social_accounts
	elif isinstance(lead, tuple):
		profile = {}
		reason = ""
		if isinstance(lead[0], FacebookContact):
			contact = lead[0]
			prospect = lead[1]
		else:
			contact = lead[1]
			prospect = lead[0]	
		profile_info = contact.get_profile_info
		if not prospect.get_location and not contact.get_location:
			print "no location"
			return False		
		if locales:
			if prospect.get_location and prospect.get_location.split(", ")[-1] not in locales and (not contact.get_location or contact.get_location.split(", ")[-1] not in locales): 
				print prospect.get_location + " not local " 
				return False
			if contact.get_location and contact.get_location.split(", ")[-1] not in locales and (not prospect.get_location or prospect.get_location.split(", ")[-1] not in locales): 
				print contact.get_location + " not local " 
				return False
		if geopoint:
			if prospect.get_location: 
				location = prospect.get_location
				miles_p = miles_apart(geopoint, location)
				if (miles_p>75 or miles_p is None) and not contact.get_location: 				
					print prospect.get_location + " not local " 
					return False
			if contact.get_location and (not prospect.get_location or miles_p > 75 or miles_p is None): 
				location = contact.get_location
				miles_c = miles_apart(geopoint, location)
				if (miles_c>75 or miles_c is None): 				
					print contact.get_location + " not local " 
					return False				
		if profile_info.get("job_company") and profile_info.get("job_company").split(",")[0] in exclude:
			print profile_info.get("job_company") + " at the same company"
			return False
		if prospect.current_job and prospect.current_job.company and prospect.current_job.company.name in exclude: 
			print prospect.current_job.company.name + " at the same company " 
			return False
		prospect_has_job = prospect.current_job and (prospect.current_job.end_date is None or prospect.current_job.end_date >= datetime.date.today())
		prospect_salary = prospect.current_job.get_max_salary if prospect.current_job else None
		contact_salary = contact.get_max_salary 
		contact_has_job = profile_info.get("job_title") and profile_info.get("job_title").find("Former") != 0  and profile_info.get("job_title").find("Worked") != 0
		salary = max(contact_salary, prospect_salary)
		if salary < min_salary:
			if not contact_has_job and not prospect_has_job:
				print "no job " + contact.facebook_id + " " + prospect.url
				return False
			if salary>0 and (prospect.current_job.start_date and (datetime.date.today() - prospect.current_job.start_date).days < 365*3):
				if contact_salary: reason = reason +  str(contact_salary) + " too low for " + profile_info.get("job_title"," ") + " " + profile_info.get("job_company"," ")
				if prospect_salary: reason += reason +  str(prospect_salary) + " too low for " + prospect.current_job.title
				print reason	
				return False		
		if profile_info.get("job_title") and re.search("Intern(,|\s|$)",profile_info.get("job_title")) and not prospect_has_job:
			print profile_info.get("job_title") + " not a real job"
			return False			
		if prospect.current_job and prospect.current_job.title and re.search("Intern(,|\s|$)",prospect.current_job.title) and not contact_has_job:
			print prospect.current_job.title + " not a real job"
			return False				
		contact_profile = clean_profile(contact.build_profile)
		if contact_profile.get("job") and contact_profile.get("job").find("Former") == 0: contact_profile.pop("job",None)
		prospect_profile = clean_profile(prospect.build_profile)
		if contact_profile.get("image_url") and prospect_profile.get("image_url"): contact_profile.pop("image_url",None)
		social_accounts = list(set(contact.social_accounts + prospect.social_accounts))
		profile.update(contact_profile)
		profile.update(prospect_profile)
		profile["location"] = location
		if salary>0: profile["salary"] = salary
		prospect_schools = [school.name for school in prospect.schools]

	if salary is None or salary == -1: salary = 0
	n_social_accounts = len(social_accounts)
	score = n_social_accounts + salary/30000 
	amazon = get_specific_url(social_accounts, type="amazon.com")
	if amazon: score += 2	
	if not profile.get("image_url"): 
		profile["image_url"] = "https://myspace.com/common/images/user.png"
		score-=5
	if profile.get("school") not in schools: profile.pop("school", None)
	if not profile.get("school") and prospect_schools: 
		common_schools = set(prospect_schools) & set(schools)
		if common_schools:
			profile["school"] = common_schools.pop()
			score+=1
	if profile.get("job") and profile.get("job").find("Financial") > -1: score-=4
	profile.update({"leadscore":score})
	return profile


def collegeGrad(prospect):
	vals = None, None
	for education in prospect.schools: 
		if education.school_linkedin_id and education.end_date: 
			return education.end_date, education.linkedin_school.name
	for education in prospect.schools: 
		if education.school_linkedin_id: 
			return None, education.linkedin_school.name			
	return vals

def link_exists(url):
	try:
		response = requests.head(url,headers=headers)
		if response.status_code != 200: return False	
	except:	return False
	return True

def clean_profile(profile):
	clean = profile
	for key in profile.keys():
		value = profile[key]
		if not value and value != 0: 
			clean.pop(key,None)
			continue
		if not isinstance(value, basestring): continue
		if value.find("http") == 0:
			if not link_exists(value): clean.pop(key,None)	
	return clean

def leadScore(prospect):
	valid_school = False
	for education in prospect.schools: 
		if education.school_linkedin_id: valid_school = True
	if not valid_school and not prospect.image_url and prospect.connections < 500: return 1
	if valid_school and prospect.image_url and prospect.connections==500: return 3
	return 2

def valid_first_degree(prospect, contact_friend):
	if not prospect or not contact_friend or not contact_friend.linkedin_id: return False
	if prospect.json.get("first_degree_linkedin_ids") and str(contact_friend.linkedin_id) in prospect.json["first_degree_linkedin_ids"]: return True
	if prospect.json.get("first_degree_urls") and contact_friend.url in prospect.json["first_degree_urls"]: return True
	if prospect.json.get("boosted_ids") and str(contact_friend.linkedin_id) in prospect.json["boosted_ids"]: return True
	return False


def compute_stars(contact_profiles):
	all_scores = [profile.get("leadscore") for profile in contact_profiles]
	for i in range(len(contact_profiles)):
		profile = contact_profiles[i]
		percentile = stats.percentileofscore(all_scores, profile["leadscore"])
		if percentile > 66: score = 3
		elif percentile > 33: score = 2
		else: score = 1
		profile["score"] = score
		contact_profiles[i] = profile
	contact_profiles = sorted(contact_profiles, key=lambda k: k['leadscore'], reverse=True)	
	return contact_profiles

def valid_second_degree(prospect, contact, contact_friend):
	return prospect and contact and contact_friend and contact_friend.connections>20 and contact.connections>20 and valid_lead(contact_friend) and has_common_institutions(contact_friend, contact) and not valid_first_degree(prospect, contact_friend)


def facebook_to_linkedin_by_name(linkedin_contacts, facebook_contacts):
	names = {}
	facebook_to_linkedin = {}
	for linkedin_contact in linkedin_contacts:
		linkedin_name = linkedin_contact.name.lower()
		for word in linkedin_name.split(" "):
			cts = names.get(word, [])
			cts.append(linkedin_contact)
			names[word] = cts
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
	return facebook_to_linkedin	

def facebook_to_bing_urls(facebook_contacts, facebook_to_linkedin):
	urls_xwalk = {}
	for facebook_contact in facebook_contacts:
		if facebook_to_linkedin.get(facebook_contact.facebook_id): continue
		name = facebook_contact.get_profile_info.get("name")
		job_title = facebook_contact.get_profile_info.get("job_title") 
		if job_title in ["Works","Worked"]: job_title = None
		job_company = facebook_contact.get_profile_info.get("job_company")
		school_name = facebook_contact.get_profile_info.get("school_name")
		school_major = facebook_contact.get_profile_info.get("school_major")
		new_urls = set()
		if job_company: 
			urls = search_linkedin_by_name(name, school=job_company, page_limit=22, limit=1000)
			new_urls.update(urls)
		if job_title: 
			urls = search_linkedin_by_name(name, school=job_title, page_limit=22, limit=1000)
			new_urls.update(urls)
		if school_major: 
			urls = search_linkedin_by_name(name, school=school_major, page_limit=22, limit=1000)
			new_urls.update(urls)
		if school_name: 
			urls = search_linkedin_by_name(name, school=school_name, page_limit=22, limit=1000)
			new_urls.update(urls)	
		urls_xwalk[facebook_contact.facebook_id] = new_urls
	return urls_xwalk

def facebook_to_linkedin_from_urls(facebook_contacts, urls_xwalk):
	facebook_to_linkedin = {}
	for facebook_contact in facebook_contacts:
		urls = urls_xwalk.get(facebook_contact.facebook_id)
		if not urls: continue
		name = facebook_contact.get_profile_info.get("name")
		facebook_words = set(name.lower().split(" "))
		job_title = facebook_contact.get_profile_info.get("job_title") 
		if job_title in ["Works","Worked"]: job_title = None
		job_company = facebook_contact.get_profile_info.get("job_company")
		school_name = facebook_contact.get_profile_info.get("school_name")
		school_major = facebook_contact.get_profile_info.get("school_major")
		found_match = False
		for url in urls:
			li = from_url(url)
			if not li: continue
			linkedin_name = li.name.lower()
			intersect = facebook_words & set(linkedin_name.split(" "))
			if len(intersect)<2: continue 			
			if job_company or job_title: 
				for job in li.jobs:
					if job_company and job.company and job.company.name and name_match(job_company, job.company.name):
						print job_company + "-->" + job.company.name
						facebook_to_linkedin[facebook_contact.facebook_id] = li.linkedin_id
						found_match = True
						break
					if job_title and job.title and name_match(job_title, job.title):
						print job_title + "-->" + job.title
						facebook_to_linkedin[facebook_contact.facebook_id] = li.linkedin_id
						found_match = True
						break						
			if found_match: break
			if school_major or school_name:
				for school in li.schools:
					if school_major and school.degree and name_match(school.degree, school_major):
						print school_major + "-->" + school.degree
						facebook_to_linkedin[facebook_contact.facebook_id] = li.linkedin_id
						found_match = True
						break
					if school_name and school.name and name_match(school.name, school_name):
						print school_name + "-->" + school.name
						facebook_to_linkedin[facebook_contact.facebook_id] = li.linkedin_id
						found_match = True
						break
			if found_match: break
	return facebook_to_linkedin

def get_phone_number(profile, liscraper):
	if profile.get("phone"): return profile.get("phone")
	li = None
	if profile.get("linkedin"): li = from_url(profile.get("linkedin"))
	phone = ""
	headquarters = ""
	website = ""
	mapquest_coordinates = ""
	mapquest = ""
	company_name = ""
	li_company = None
	location = ""
	if li:
		if li.current_job:
			li_company = li.current_job.linkedin_company
			if not li_company and li.current_job.company:
				results = search_linkedin_companies(li.current_job.company.name)
				if results: 
					company_url = results[0]
					li_company = company_from_url(company_url)
		location = li.current_job.location if li.current_job and li.current_job.location else li.location_raw
	else: 
		results = search_linkedin_companies(profile.get("company"))
		if results: 
			company_url = results[0]
			li_company = company_from_url(company_url)		
		fbcontact = session.query(FacebookContact).get(profile.get("facebook").split("/")[-1])
		location = fbcontact.get_location
	company_name = li_company.name if li_company else profile.get("company")
	if li_company:
		if li_company.website: website = li_company.website.replace("https://","").replace("http://","").split("/")[0]
		if li_company.headquarters: headquarters = li_company.headquarters.replace("\n"," ")	
	if location:
		mapquest = get_mapquest_coordinates(location)
		if mapquest and mapquest.get("latlng_result",{}).get("name"): mapquest_coordinates = mapquest.get("latlng_result",{}).get("name")
	queries = ["+".join([company_name,mapquest_coordinates])]
	if website: queries = ["+".join([website, company_name, mapquest_coordinates]),"+".join([website,mapquest_coordinates])] + queries + ["+".join([website,company_name,headquarters]),"+".join([website,headquarters]),"+".join([company_name,headquarters]),"+".join([website, company_name]),website] 
	for q in queries:
		if q.endswith("+") or q.startswith("+"): 
			continue
		google_results = get_google_results(liscraper, q)	
		if google_results.phone_numbers and len(set(google_results.phone_numbers))==1 and len(set(google_results.plus_links))==1: 
			phone = google_results.phone_numbers[0]
			#print query
			return phone
		elif len(google_results.phone_numbers)==len(google_results.plus_links):
			for k in xrange(0, len(google_results.plus_links)):
				plus_link = google_results.plus_links[k]
				bing_results = query("", site="%22" + plus_link + "%22").results
				if not bing_results: continue
				bing_title = bing_results[0].get("Title").replace(' - About - Google+','')
				if name_match(bing_title, company_name):
					phone = google_results.phone_numbers[k]
					#print company_name + " " + plus_link
					#break
					return phone
		else: 
			for k in xrange(0, len(google_results.plus_links)):
				plus_link = google_results.plus_links[k]
				bing_results = query("", site="%22" + plus_link + "%22").results
				if not bing_results: continue
				bing_title = bing_results[0].get("Title").replace(' - About - Google+','')
				if name_match(bing_title, company_name):
					response = requests.get(plus_link, headers=headers)
					source = response.content
					# try:
					# 	liscraper.driver.get(plus_link)
					# except:
					# 	liscraper.login()
					# 	liscraper.driver.get(plus_link)
					# source = liscraper.driver.page_source
					phone_numbers = re.findall('\([0-9]{3}\) [0-9]{3}\-[0-9]{4}',source)
					if phone_numbers: return phone_numbers[0]
	if li_company:
		clearbit_response = li_company.get_clearbit_response
		if clearbit_response: 
			phone = clearbit_response.get("phone")	
			if phone: return phone
	if li:
		pipl_json = li.get_pipl_response
		if pipl_json: 
			pipl_valid_recs = []
			for record in pipl_json.get("records",[]) + [pipl_json.get("person",{})]:
				if not record.get('@query_params_match',True): continue
				pipl_valid_recs.append(record)
			pipl_json_str = json.dumps(pipl_valid_recs)
			if re.search('\([0-9]{3}\) [0-9]{3}\-[0-9]{4}',pipl_json_str):
				phone = re.search('\([0-9]{3}\) [0-9]{3}\-[0-9]{4}',pipl_json_str).group(0)
				#print li.url	
				return phone
	return phone

def get_mailto(profile):
	if profile.get("mailto"): return profile.get("mailto")
	all_emails = set()
	if profile.get("linkedin"): 
		li = from_url(profile.get("linkedin"))
		if li: 
			emails = get_pipl_emails(li.get_pipl_response)
			if emails: all_emails.update(emails)
	if profile.get("facebook"): 
		fb = session.query(FacebookContact).get(profile.get("facebook").split("/")[-1])
		if fb: 
			emails = get_pipl_emails(fb.get_pipl_response)
			if emails: all_emails.update(emails)	
	if all_emails:
		mailto = 'mailto:' + ",".join(list(all_emails))	
		return mailto
	return None		