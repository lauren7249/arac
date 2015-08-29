from consume.facebook_friend import *
from prime.prospects.models import *
from prime.prospects.get_prospect import *
from prime.utils.networks import *
from prime.utils.googling import *

refresh = False
min_salary = 30000
fbscraper = FacebookFriend()

client_linkedin_id='103258031' 
client_linkedin_contact = from_linkedin_id(client_linkedin_id)
client_json = client_linkedin_contact.json

facebook_linkedin_friends = []

#agents facebook info
client_facebook_id='chris.biren'
client_facebook_contact = fbscraper.get_facebook_contact("https://www.facebook.com/" + client_facebook_id, scroll_to_bottom=True)
client_facebook_profile = client_facebook_contact.get_profile_info
client_facebook_location = client_facebook_profile.get("lives_in")
client_facebook_state = client_facebook_location.split(", ")[-1]
client_engagers = client_facebook_contact.get_recent_engagers
client_engagers = fbscraper.get_likers(client_facebook_contact)
client_engagers = client_facebook_contact.top_engagers #75


if refresh:
	#999
	#parse raw emails from files
	import re
	emails = set()
	email_regex = "[A-Za-z0-9\.]+@[A-Za-z0-9]+\.[a-zA-Z0-9]+"
	f = open("/Users/lauren/Downloads/google contacts.csv")
	for line in f.readlines():
		if not re.search(email_regex,line): continue
		email = re.search(email_regex,line).group(0)
		if email: emails.add(email)
	f = open("/Users/lauren/Downloads/yahoo_contacts.csv")
	for line in f.readlines():
		if not re.search(email_regex,line): continue
		email = re.search(email_regex,line).group(0)
		if email: emails.add(email)	


	#check apis and save results
	from prime.prospects.models import EmailContact, session
	emails_contacts = []
	for email in emails:
		contact = session.query(EmailContact).get(email)
		if not contact: contact = EmailContact(email=email)
		vibe_response = contact.get_vibe_response
		if vibe_response.get("name") == 'Not a Person': 
			session.add(contact)
			session.commit()
			continue	
		contact.get_fullcontact_response
		pipl_response = contact.get_pipl_response
		contact.get_fullcontact_response
		session.add(contact)
		session.commit()	
		if len(contact.social_accounts) == 0: 
			continue		
		emails_contacts.append(email)

	#look for relevant social profiles
	email_linkedin_friend_links = []
	email_facebook_friend_links = []
	for email in emails:
		contact = session.query(EmailContact).get(email)
		if not contact: continue
		social_accounts = contact.social_accounts
		facebook_link = get_specific_url(social_accounts, "facebook.com")
		linkedin_link = get_specific_url(social_accounts, "linkedin.com")
		if facebook_link: email_facebook_friend_links.append(facebook_link)
		if linkedin_link: email_linkedin_friend_links.append(linkedin_link)

	email_facebook_friends = []
	for link in set(email_facebook_friend_links):
		contact = fbscraper.get_facebook_contact(link)
		if not contact: continue
		username = contact.facebook_id
		email_facebook_friends.append(username)
		print len(email_facebook_friends)
	email_facebook_friends = list(set(email_facebook_friends))	

	client_json["email_facebook_ids"] = email_facebook_friends
	client_linkedin_contact.json = client_json
	session.add(client_linkedin_contact)
	session.commit()

	for linkedin_url in set(email_linkedin_friend_links):
		r.sadd("urls",linkedin_url)

	#after scraping
	#248
	email_linkedin_friends = []
	for linkedin_url in set(email_linkedin_friend_links):
		contact_linkedin = from_url(linkedin_url)
		if contact_linkedin: email_linkedin_friends.append(str(contact_linkedin.linkedin_id))

	client_json["email_linkedin_ids"] = email_linkedin_friends
	client_linkedin_contact.json = client_json
	session.add(client_linkedin_contact)
	session.commit()

client_engagers = facebook_friends & client_engagers #65

valid_locations = ['Colorado','Colorado Area','Greater Denver Area', client_facebook_state]
exclusions = [client_facebook_profile.get("job_company"), client_linkedin_contact.current_job.company.name, 'New York Life']


extended_facebook_network = {}
for username in client_facebook_contact.get_friends:
	scroll_to_bottom = username in client_engagers
	contact = fbscraper.get_facebook_contact("https://www.facebook.com/" + username, scroll_to_bottom=scroll_to_bottom)
	fbscraper.get_likers(contact)
	contact_linkedin_url = get_specific_url(contact.social_accounts, type="linkedin.com")
	if contact_linkedin_url: 
		contact_linkedin = from_url(contact_linkedin_url)
		if contact_linkedin: facebook_linkedin_friends.append(str(contact_linkedin.linkedin_id))
#agents linkedin info
linkedin_friends = client_json["first_degree_linkedin_ids"]


client_json["facebook_friend_linkedin_ids"] = facebook_linkedin_friends
client_linkedin_contact.json = client_json
session.add(client_linkedin_contact)
session.commit()

linkedin_friends = client_linkedin_contact.json["first_degree_linkedin_ids"]

#565
linkedin_friends = set(client_json["email_linkedin_ids"] + client_json["facebook_friend_linkedin_ids"] + client_json["first_degree_linkedin_ids"])
linkedin_contacts = []
for friend in linkedin_friends:
	contact = from_linkedin_id(friend)
	if not contact: 
		print " not found " + friend
		continue
	linkedin_contacts.append(contact)

#529
facebook_contacts = []
facebook_friends = set(client_json["email_facebook_ids"] + client_facebook_contact.get_friends)
for friend in facebook_friends:
	contact = session.query(FacebookContact).get(friend)
	if not contact: continue
	facebook_contacts.append(contact)

#matching together li and fb
names = {}
for linkedin_contact in linkedin_contacts:
	linkedin_name = linkedin_contact.name.lower()
	for word in linkedin_name.split(" "):
		cts = names.get(word, [])
		cts.append(linkedin_contact)
		names[word] = cts
all_contacts = []
matching_linkedin_ids = []
for facebook_contact in facebook_contacts:
	if not facebook_contact.get_profile_info: continue
	facebook_name = facebook_contact.get_profile_info.get("name").lower()
	facebook_words = set(facebook_name.split(" "))
	linkedin_match = False
	matching_linkedin_contacts = []
	for word in facebook_words:	
		for linkedin_contact in names.get(word, []):
			matching_linkedin_contacts.append(linkedin_contact)
	for linkedin_contact in matching_linkedin_contacts:
		linkedin_name = linkedin_contact.name.lower()
		intersect = facebook_words & set(linkedin_name.split(" "))
		if len(intersect)>=2: 
			print facebook_name + " == " + linkedin_name
			facebook_contact.prospect_id = linkedin_contact.id
			facebook_contact.linkedin_id = linkedin_contact.linkedin_id
			session.add(facebook_contact)
			session.commit()			
			all_contacts.append((facebook_contact,linkedin_contact))
			matching_linkedin_ids.append(linkedin_contact.linkedin_id)
			linkedin_match = True
			break
	if not linkedin_match: 
		all_contacts.append(facebook_contact)

#all_contacts = 510
#matching_linkedin_contacts = 177

for linkedin_contact in linkedin_contacts:
	if linkedin_contact.linkedin_id not in matching_linkedin_ids: all_contacts.append(linkedin_contact)

#all_contacts = 899

contact_profiles = []
n_valid=0
for contact in all_contacts:
	valid_profile = valid_lead(contact, locales=valid_locations, exclude=exclusions, min_salary=min_salary)
	if valid_profile:
		n_valid+=1
		contact_profiles.append(valid_profile)


contact_profiles = compute_stars(contact_profiles)

extended_facebook_network = {}
for facebook_contact in facebook_contacts:
	try:
		if not facebook_contact.get_recent_engagers: continue
	except:
		continue
	engagers = set([item for sublist in facebook_contact.get_recent_engagers.values() for item in sublist])
	for engager in engagers:
		if engager in facebook_friends or engager == client_facebook_id or engager == '': continue
		recs = extended_facebook_network.get(engager, [])
		recs.append(facebook_contact.facebook_id)
		extended_facebook_network.update({engager: recs})
	print len(extended_facebook_network)

import joblib
extended_facebook_network = joblib.load('extended_facebook_network')
extended_profiles = []
api_hits = 0
for username in extended_facebook_network:
	contact = fbscraper.get_facebook_contact("https://www.facebook.com/" + username)
	if not contact: continue
	valid_profile = valid_lead(contact, locales=valid_locations, exclude=exclusions, min_salary=min_salary)
	if valid_profile:
		introducer_username = extended_facebook_network[valid_profile.get("id")]
		introducer_contact = session.query(FacebookContact).get(introducer_username)
		image_url = introducer_contact.get_profile_info.get("image_url")
		name = introducer_contact.get_profile_info.get("name")
		valid_profile["introducer_url"] = image_url
		valid_profile["introducer_name"] = name		
		extended_profiles.append(valid_profile)
		continue
	if contact.get_profile_info.get("lives_in") and contact.get_profile_info.get("lives_in").split(", ")[-1] not in valid_locations: continue
	api_hits+=1
	contact_linkedin_url = get_specific_url(contact.social_accounts, type="linkedin.com")
	if not contact_linkedin_url: continue
	contact_linkedin = from_url(contact_linkedin_url)
	if not contact_linkedin: continue
	valid_profile = valid_lead((contact,contact_linkedin), locales=valid_locations, exclude=exclusions, min_salary=min_salary)
	if valid_profile:
		introducer_username = extended_facebook_network[valid_profile.get("id")]
		introducer_contact = session.query(FacebookContact).get(introducer_username)
		image_url = introducer_contact.get_profile_info.get("image_url")
		name = introducer_contact.get_profile_info.get("name")
		valid_profile["introducer_url"] = image_url
		valid_profile["introducer_name"] = name			
		extended_profiles.append(valid_profile)	

extended_profiles = compute_stars(extended_profiles)
print json.dumps(extended_profiles)