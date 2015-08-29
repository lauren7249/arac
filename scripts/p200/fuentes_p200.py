linkedin_id='147893054' #fuentes
from prime.prospects.get_prospect import *
from prime.utils.googling import *
from prime.utils import r
from prime.utils.networks import *
prospect = from_linkedin_id(linkedin_id)

#60
friends = prospect.json["first_degree_linkedin_ids"]

#57
prospects = []
for friend in friends:
	p = from_linkedin_id(friend)
	if p: prospects.append(p)
#30
new_york_employed = agent_network(prospects)


# for contact in new_york_employed:
# 	u = search_extended_network(contact, limit=300)
# 	for key in u.keys():
# 		r.sadd("urls",key)

#1175 links, #1165 connections, #34 extended network connections
extended_network = {}
for contact in new_york_employed:
	for key in contact.google_network_search.keys():
		contact_friend = from_url(key)
		if valid_second_degree(prospect, contact, contact_friend): extended_network.update({contact_friend: contact.id})

#20 
extended = []
influencers = []
influencer_ids =[]
for potential_contact in extended_network.keys():
	if leadScore(potential_contact) > 1 and potential_contact.image_url and potential_contact.url not in ["http://www.linkedin.com/pub/chris-serino/7/a91/32b", "https://www.linkedin.com/pub/matthew-weinreb/19/616/82"]:
		introducer = from_prospect_id(extended_network[potential_contact])
		intro = {"id":potential_contact.id, "name":potential_contact.name, "job":potential_contact.current_job.title, "company":potential_contact.current_job.company.name, "score":leadScore(potential_contact), "image_url": potential_contact.image_url if potential_contact.image_url else "", "url":potential_contact.url, "introducer_url": introducer.url, "introducer_image_url":introducer.image_url, "introducer_name":introducer.name}
		extended.append(intro)
		if introducer.url not in influencer_ids:
			influencer_ids.append(introducer.url)
			i = {"introducer_url": introducer.url, "introducer_image_url":introducer.image_url, "introducer_name":introducer.name}
			influencers.append(i)

jon = prospect
demo = []
for prospect in new_york_employed:
	score = leadScore(prospect)
	if prospect.image_url: secret_score = score + 1 
	else: secret_score = score
	d = {"id":prospect.id, "name":prospect.name, "job":prospect.current_job.title, "company":prospect.current_job.company.name, "score":score, "image_url": prospect.image_url if prospect.image_url else "", "url":prospect.url, "secret_score" : secret_score}
	demo.append(d)
demo = sorted(demo, key=lambda k: k['secret_score'], reverse=True)
print json.dumps(demo)	






  
