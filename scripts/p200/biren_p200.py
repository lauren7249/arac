linkedin_id='103258031' 
from prime.prospects.get_prospect import *
from prime.utils.googling import *
from prime.utils import r, headers
from prime.utils.networks import agent_network, valid_lead
from consume.linkedin_friend import *
from prime.prospects.models import *
import requests, json

prospect = from_linkedin_id(linkedin_id)

if not prospect:
	ig = LinkedinFriend(username="jeff@advisorconnect.co", password="1250downllc")
	ig.login()

	#333
	friends = set(ig.get_second_degree_connections(linkedin_id))

	#301
	friend_urls = []
	for friend in friends:
		url = ig.get_public_link(friend)
		if url and len(url): friend_urls.append(url)

	#nope
	propsect = from_url("https://www.linkedin.com/in/chrisbiren")
	#post scrape - works
	prospect = from_linkedin_id(linkedin_id)

	prospect_json = prospect.json
	prospect_json["first_degree_linkedin_ids"] = list(friends)
	prospect_json["first_degree_urls"] = friend_urls
	session.query(Prospect).filter_by(id=prospect.id).update({"json":prospect_json})
	session.commit()
	for url in friend_urls:
		r.sadd("urls",url)

#333
friends = prospect.json["first_degree_linkedin_ids"]

#319
prospects = []
for friend in friends:
	p = from_linkedin_id(friend)
	if p: prospects.append(p)


valid_locations = ['Colorado','Colorado Area','Greater Denver Area']
#158 - with job, in valid areas, not in financial services or insurance
network = agent_network(prospects, locales=valid_locations)

from consume.facebook_friend import *
ig = FacebookFriend()
ig.login()

#270
facebook = ig.get_second_degree_connections("chris.biren/friends")

#114 work, 45 obviously in colorado
for person in facebook:
	role = facebook[person].get("role")
	facebook[person]["local"] = None
	if role:
		if role.find("Works") >=0 or role.find(" at ")>=0: facebook[person]["works"] = True
		if role.find("Colorado") >= 0: facebook[person]["local"] = True

#89 in colorado
for person in facebook:
	if facebook[person].get("local") is None:
		link = "https://www.facebook.com/" + facebook[person].get("username")
		ig.driver.get(link)
		try:
			lives_in = ig.driver.find_element_by_xpath(".//div[contains(text(),'Lives in')]").text
			if lives_in: facebook[person]["local"] = lives_in.find("Colorado") > 0
		except:
			continue

#10% hit rate for linkedin
#106 local now
pipl = "http://api.pipl.com/search/v3/json/?key=uegvyy86ycyvyxjhhbwsuhj9&pretty=true&username="
for person in facebook:
	if facebook[person].get("local") in [None, True]:
		if facebook[person].get("local") is None or facebook[person].get("works") is None:
			username = facebook[person].get("username")
			piplrecord = session.query(FacebookContact).get(username)
			pipl_json = None
			if piplrecord is None:
				linkedin_url = None
				req = pipl + username + "@facebook"
				response = requests.get(req, headers=headers, verify=False)
				if response.status_code == 200:
					pipl_json = json.loads(response.content)
					for record in pipl_json.get("records"):
						if record.get('@query_params_match'):
							if record.get("source").get("domain") == "linkedin.com":
								linkedin_url = record.get("source").get("url")
								r.sadd("urls",linkedin_url) #for scraper										
					piplrecord = FacebookContact(facebook_id=username, linkedin_url=linkedin_url, pipl_response=pipl_json)
					session.add(piplrecord)
					session.commit()
			else: 
				pipl_json = piplrecord.pipl_response
			if pipl_json:
				for record in pipl_json.get("records"):
					if record.get('@query_params_match'):				
						for address in  record.get("addresses",[]):
							if address.get("state") == "CO": facebook[person]["local"] = True

#this added 4 people
for person in facebook:
	if facebook[person].get("local") is None or facebook[person].get("works") is None:
		username = facebook[person].get("username")
		piplrecord = session.query(FacebookContact).get(username)
		if piplrecord:		
			linkedin_url = piplrecord.linkedin_url
			if linkedin_url:
				prospect = from_url(linkedin_url)
				if prospect and valid_lead(prospect, valid_locations): 
					facebook[person]["local"] = True
					facebook[person]["works"] = True
					network.append(prospect)
					print prospect
# #manually check google results -- only 9 incremental and they are not kosher
# for person in facebook:
# 	if facebook[person].get("local") and facebook[person].get("works") is None:
# 		name = facebook[person].get("name")
# 		if not name: 
# 			print person
# 			continue
# 		role = facebook[person].get("role", "")
# 		if not role: continue
# 		terms =  name + " " + role 
# 		u = search_linkedin_profile(terms, name)
# 		if u: 
# 			prospect = from_url(u)
# 			if prospect and valid_lead(prospect, valid_locations) and len(lead_ids.intersection(set([prospect.id])))==0: 
# 				print prospect.url + "    " + facebook[person].get("username")

#54 people working in colorado

for person in facebook:
	username = facebook[person].get("username")
	if session.query(Facebook).get(username) is None:
		fb = Facebook(facebook_id =username , info={"role":facebook[person].get("role"), "name":facebook[person].get("name")} )
		for lead in prospects:
			intersect = set(facebook[person].get("name").lower().split(" ")) & set(lead.name.lower().split(" "))
			if len(intersect)>=2: 
				fb.prospect_id = lead.id
				fb.linkedin_id = lead.linkedin_id
				break
		session.add(fb)
		session.commit()
		


valid_locations = ['Colorado','Colorado Area','Greater Denver Area']
#158 - with job, in valid areas, not in financial services or insurance
network = agent_network(prospects, locales=valid_locations)


for person in facebook:
	username = facebook[person].get("username")
	social_profiles = {"facebook.com":"http://www.facebook.com/" + username}
	piplrecord = session.query(FacebookContact).get(username)
	pipl_json = None
	if piplrecord is None:
		linkedin_url = None
		req = pipl + username + "@facebook"
		response = requests.get(req, headers=headers, verify=False)
		if response.status_code == 200:
			pipl_json = json.loads(response.content)
			for record in pipl_json.get("records"):
				if record.get('@query_params_match'):
					if record.get("source").get("domain") == "linkedin.com":
						linkedin_url = record.get("source").get("url")
						r.sadd("urls",linkedin_url) #for scraper										
			piplrecord = FacebookContact(facebook_id=username, linkedin_url=linkedin_url, pipl_response=pipl_json)
			session.add(piplrecord)
			session.commit()		
	else:
		pipl_json = piplrecord.pipl_response
		for record in pipl_json.get("records"):
			if record.get('@query_params_match') and record.get("source") and record.get("source").get("url"):
				domain = record.get("source").get("domain")
				if domain in ["twitter.com","soundcloud.com","slideshare.net","plus.google.com","pinterest.com","linkedin.com"]:
					link = record.get("source").get("url")			
					social_profiles.update({domain:link})
	if len(social_profiles)>0: 
		facebook[person]["social_profiles"] = social_profiles


#this is being slow
fullcontact = "http://api.fullcontact.com/v2/person.json?person.json?facebookUsername=wilk.cutabuv&apiKey=dda7318aacfcf5cd"


#158
linkedin_ids = [] 
for prospect in network:
	if prospect.linkedin_id not in linkedin_ids: 
		linkedin_ids.append(prospect.linkedin_id)
fb_count = 0
for person in facebook:
	if facebook[person].get("local") and facebook[person].get("works"):
		username = facebook[person].get("username")
		fb = session.query(Facebook).get(username) 	
		if fb and fb.linkedin_id:
			if fb.linkedin_id not in linkedin_ids: 
				linkedin_ids.append(prospect.linkedin_id)
		else: fb_count+=1
	elif facebook[person].get("local") != False: 
		linkedin_url = facebook[person].get("social_profiles",{}).get("linkedin.com")
		if linkedin_url: 
			prospect = from_url(linkedin_url)
			if not prospect:
				#r.sadd("urls",linkedin_url)
				print linkedin_url
			elif prospect.linkedin_id not in linkedin_ids and valid_lead(prospect, valid_locations):
				linkedin_ids.append(prospect.linkedin_id)
				print linkedin_url

#all good
for person in facebook:
	if facebook[person].get("local") and facebook[person].get("works"):
		if facebook[person].get("image_url") is None: print person 


for prospect in network:
	if prospect.image_url is None: 
		for account in prospect.social_accounts:
			if account.find("facebook") >=0:
				ig.driver.get(account)
				try:
					image_url = ig.driver.find_elements_by_xpath(".//div/div/div/div/div/div/div/div/div/a/img")[0].get_attribute("src")
					prospect.image_url = image_url
					session.add(prospect)
					session.commit()
				except:
					image_url = None

