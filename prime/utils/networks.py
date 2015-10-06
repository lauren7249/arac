from prime.prospects.models import *
from prime.prospects.get_prospect import *
from prime.utils.networks import *
import scipy.stats as stats
import datetime
import joblib
import re

pegasos_model = joblib.load("../data/pegasos_model.dump")

def title_qualifies(title):
	try:
		title_split = re.sub('[^A-Za-z0-9]+', ' ', title).lower().split()
	except:
		print "error"
		return False
	d = dict((i,title_split.count(i)) for i in title_split)
	dotproduct=0
	for j in d:
		if j in pegasos_model: dotproduct+=d[j]*pegasos_model[j] 
	return (dotproduct > 0)

def agent_network(prospects, locales=['New York','Greater New York City Area']):
	#employed, in ny, not in financial services
	new_york_employed = []
	for prospect in prospects:
		if valid_lead(prospect, locales=locales): new_york_employed.append(prospect)  
	return new_york_employed

def valid_lead(lead, locales=None, exclude=[], schools=[],min_salary=60000):
	prospect_schools = None
	if not lead: return False
	if isinstance(lead, Prospect):
		prospect = lead
		if prospect.current_job is None or (prospect.current_job.end_date and prospect.current_job.end_date < datetime.date.today()): 
			print "no job"
			return False
		if locales:
			location = prospect.get_location
			if not location: 
				print "no location"
				return False		
			if location.split(", ")[-1] not in locales:
				print location + " not local" 
				return False
		if prospect.current_job.company.name in exclude: 
			print prospect.current_job.company.name + " at the same company " 
			return False
		salary = prospect.get_max_salary
		if salary>0 and salary < min_salary and (prospect.current_job.start_date and (datetime.date.today() - prospect.current_job.start_date).days < 365*3): 
			print str(salary) + " too low for " + prospect.current_job.title 
			return False	
		profile = clean_profile(prospect.build_profile)	
		prospect_schools = [school.name for school in prospect.schools]
		social_accounts = prospect.social_accounts
	elif isinstance(lead, FacebookContact):
		contact = lead
		profile_info = contact.get_profile_info
		if not profile_info:
			print "no profile info for " + contact.facebook_id
		if locales:
			location = contact.get_location
			if not location: 
				print "no location"
				return False
			if location.split(", ")[-1] not in locales:
				print location + " not local"
				return False			
		if profile_info.get("job_company") and profile_info.get("job_company").split(",")[0] in exclude :
			print profile_info.get("job_company") + " at the same company"
			return False
		# if profile_info.get("job_title") is None:
		# 	print "no job title for " + contact.facebook_id
		# 	return False
		salary = contact.get_max_salary if profile_info.get("job_title") and profile_info.get("job_title").find("Former") != 0 else None
		if not salary and (not profile_info.get("job_title") or profile_info.get("job_title")=='Worked' or profile_info.get("job_title").find("Former") == 0):
			print "no job"
			return False
		if salary>0 and salary < min_salary and profile_info.get("job_title") != "Works":
			print str(salary) + " too low for " + profile_info.get("job_title")
			return False
		profile = clean_profile(contact.build_profile)
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
		if locales:
			location = prospect.get_location if prospect.get_location else contact.get_location
			if not location:
				print "no location"
				return False
			if location.split(", ")[-1] not in locales: 
				reason = location + " not local " 
				location = contact.get_location
				if not location: 
					print reason
					return False
				if location.split(", ")[-1] not in locales: 
					reason = reason + " and " + location.split(", ")[-1] + " not local"
					print reason
					return False
		if profile_info.get("job_company") and profile_info.get("job_company").split(",")[0] in exclude:
			print profile_info.get("job_company") + " at the same company"
			return False
		if prospect.current_job and prospect.current_job.company and prospect.current_job.company.name in exclude: 
			print prospect.current_job.company.name + " at the same company " 
			return False
		prospect_salary = prospect.current_job.get_max_salary if prospect.current_job and prospect.current_job.get_max_salary and (prospect.current_job.end_date is None or prospect.current_job.end_date > datetime.date.today()) else None
		contact_salary = contact.get_max_salary if profile_info.get("job_title") and profile_info.get("job_title").find("Former") != 0 else None
		salary = max(contact_salary, prospect_salary)
		if salary < min_salary and (not prospect.current_job or not prospect.current_job.title or (prospect.current_job.end_date and prospect.current_job.end_date < datetime.date.today())) and profile_info.get("job_title") != "Works":
			if profile_info.get("job_title"): reason = reason +  str(contact_salary) + " too low for " + profile_info.get("job_title")
			else: reason = "no job"
			print reason	
			return False		
		if salary>0 and salary < min_salary and (prospect.current_job.start_date and (datetime.date.today() - prospect.current_job.start_date).days < 365*3): 
			if prospect.current_job.title: reason = str(prospect_salary) + " too low for " + prospect.current_job.title + ". "
			if profile_info.get("job_title"): reason = reason +  str(contact_salary) + " too low for " + profile_info.get("job_title")
			print reason
			return False	
		contact_profile = clean_profile(contact.build_profile)
		if contact_profile.get("job") and contact_profile.get("job").find("Former") == 0: contact_profile.pop("job",None)
		prospect_profile = clean_profile(prospect.build_profile)
		if contact_profile.get("image_url") and prospect_profile.get("image_url"): contact_profile.pop("image_url",None)
		social_accounts = list(set(contact.social_accounts + prospect.social_accounts))
		profile.update(prospect_profile)
		profile.update(contact_profile)
		prospect_schools = [school.name for school in prospect.schools]

	if salary is None: salary = 0
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
	if profile.get("job","").find("Financial") > -1: score-=4
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

def clean_profile(profile):
	for key in profile.keys():
		value = profile[key]
		if not value: 
			profile.pop(key,None)
			continue
		if not isinstance(value, basestring): continue
		if value.find("http") == 0 or key.find("url")>-1:
			try:
				response = requests.get(value,headers=headers)
				if response.status_code != 200: profile.pop(key,None)	
			except:
				profile.pop(key,None)	
	return profile

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