linkedin_id='147893054' #fuentes
from prime.prospects.get_prospect import *
from prime.utils.googling import *
from prime.utils import r
prospect = from_linkedin_id(linkedin_id)

friends = prospect.json["first_degree_linkedin_ids"]

p200 = []
for friend in friends:
    f = from_linkedin_id(friend)
    if f and f.industry_raw != "Financial Services" and f.industry_raw != "Insurance": 
        if f.current_job: print f.url

u = search_extended_network(prospect, limit=300)
#for scraper
for key in u.keys() +  prospect.json["people"]:
    r.sadd("urls",key)

for key in u.keys() + prospect.json["people"]:
    them = from_url(key)
    if them:
    	if has_common_institutions(prospect, them): print key   
