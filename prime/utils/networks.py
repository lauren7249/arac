from prime.prospects.models import *
from prime.prospects.get_prospect import *
from prime.utils.networks import *

def agent_network(prospects, locales=['New York','Greater New York City Area']):
	#employed, in ny, not in financial services
	new_york_employed = []
	for prospect in prospects:
		if valid_lead(prospect, locales=locales): new_york_employed.append(prospect)  
	return new_york_employed

def valid_lead(lead, locales=['New York','Greater New York City Area'], exclude=['Insurance','Financial Services'], min_salary=60000):
	if not lead: return False
	if isinstance(lead, Prospect):
		prospect = lead
		if prospect.current_job is None: 
			print "no job"
			return False
		key = prospect.location_raw.split(",")[-1].strip()
		if key not in locales:
			print key + " not local" 
			return False
		if prospect.current_job.company.name in exclude: 
			print prospect.current_job.company.name + " at the same company " 
			return False
		salary = prospect.current_job.get_indeed_salary
		if salary>0 and salary < min_salary: 
			print str(salary) + " too low for " + prospect.current_job.title 
			return False	
		profile = prospect.build_profile		
		n_social_accounts = len(prospect.social_accounts)
	elif isinstance(lead, FacebookContact):
		contact = lead
		profile_info = contact.get_profile_info
		if not profile_info:
			print "no profile info for " + contact.facebook_id
		salary = contact.get_indeed_salary
		location = profile_info.get("lives_in") if profile_info.get("lives_in") else profile_info.get("from")
		if not location: 
			print "no location"
			return False
		if profile_info.get("job_company") and profile_info.get("job_company").split(",")[0] in exclude :
			print profile_info.get("job_company") + " at the same company"
			return False
		if location.split(", ")[-1] not in locales:
			print location + " not local"
			return False
		# if profile_info.get("job_title") is None:
		# 	print "no job title for " + contact.facebook_id
		# 	return False
		if not salary and not profile_info.get("job_company") and not profile_info.get("job_title"):
			print "no job"
			return False
		if salary>0 and salary < min_salary:
			print str(salary) + " too low for " + profile_info.get("job_title")
			return False
		profile = contact.build_profile
		n_social_accounts = len(contact.social_accounts)
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
		key = prospect.location_raw.split(",")[-1].strip()
		if key not in locales:
			reason = key + " not local " 
			location = profile_info.get("lives_in") if profile_info.get("lives_in") else profile_info.get("from")
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
		prospect_salary = prospect.current_job.get_indeed_salary if prospect.current_job and prospect.current_job.get_indeed_salary else 0
		contact_salary = contact.get_indeed_salary if contact.get_indeed_salary else 0
		salary = max(contact_salary, prospect_salary)
		if salary < min_salary and not prospect.current_job.title:
			if profile_info.get("job_title"): reason = reason +  str(contact_salary) + " too low for " + profile_info.get("job_title")
			else: reason = "no job"
			print reason	
			return False		
		if salary>0 and salary < min_salary: 
			if prospect.current_job.title: reason = str(prospect_salary) + " too low for " + prospect.current_job.title + ". "
			if profile_info.get("job_title"): reason = reason +  str(contact_salary) + " too low for " + profile_info.get("job_title")
			print reason
			return False	
		contact_profile = contact.build_profile
		prospect_profile = prospect.build_profile
		n_social_accounts = len(set(contact.social_accounts + prospect.social_accounts))
		if not prospect_profile.get("company"): prospect_profile.pop("company",None)
		if not prospect_profile.get("job"): prospect_profile.pop("job",None)
		if not contact_profile.get("company"): contact_profile.pop("company",None)
		if not contact_profile.get("job"): contact_profile.pop("job",None)		
		profile.update(prospect_profile)
		profile.update(contact_profile)
	if salary is None: salary = 0
	score = n_social_accounts + salary/30000 
	if not profile.get("image_url"): 
		profile["image_url"] = "https://myspace.com/common/images/user.png"
		score-=1
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

def valid_second_degree(prospect, contact, contact_friend):
	return prospect and contact and contact_friend and contact_friend.connections>20 and contact.connections>20 and valid_lead(contact_friend) and has_common_institutions(contact_friend, contact) and not valid_first_degree(prospect, contact_friend)