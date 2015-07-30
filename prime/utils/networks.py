
from prime.prospects.get_prospect import *
from prime.utils.networks import *

def agent_network(prospects):
	#employed, in ny, not in financial services
	new_york_employed = []
	for prospect in prospects:
		if valid_lead(prospect): new_york_employed.append(prospect)  
	return new_york_employed

def valid_lead(prospect):
	if prospect.current_job is None: return False
	key = prospect.location_raw.split(",")[-1].strip()
	if key in ['New York','Greater New York City Area'] and prospect.industry_raw not in ['Insurance','Financial Services']: return True
	return False

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