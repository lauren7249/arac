linkedin_id='147893054' #fuentes
from prime.prospects.get_prospect import *
from prime.utils.googling import *
from prime.utils import r
from prime.utils.networks import *
prospect = from_linkedin_id(linkedin_id)

#60
friends = prospect.json["first_degree_linkedin_ids"]

#30
new_york_employed = agent_network(friends)

for contact in new_york_employed:
	u = search_extended_network(contact, limit=300)
	for key in u.keys():
		r.sadd("urls",key)

#filter to people with > 20 connections


#for scraper
for key in u.keys() +  prospect.json["people"]:
    r.sadd("urls",key)

for key in u.keys() + prospect.json["people"]:
    them = from_url(key)
    if them:
    	if has_common_institutions(prospect, them): print key   
