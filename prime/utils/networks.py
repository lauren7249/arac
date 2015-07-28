
from prime.prospects.get_prospect import *
from prime.utils.networks import *

def agent_network(friends):
	prospects = []
	for friend in friends:
		prospect = from_linkedin_id(friend)
		if prospect: prospects.append(prospect)

	#employed, in ny, not in financial services
	new_york_employed = []
	for prospect in prospects:
		if prospect.current_job is None: continue
		key = prospect.location_raw.split(",")[-1].strip()
		if key in ['New York','Greater New York City Area'] and prospect.industry_raw not in ['Insurance','Financial Services']: new_york_employed.append(prospect)  
	return new_york_employed