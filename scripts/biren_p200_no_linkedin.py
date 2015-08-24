from consume.facebook_friend import *
from prime.prospects.models import *
from prime.prospects.get_prospect import *
from prime.utils.networks import *
from prime.utils.googling import *

refresh = False
min_salary = 40000
fbscraper = FacebookFriend()

client_linkedin_id='103258031' 
client_linkedin_contact = from_linkedin_id(client_linkedin_id)
client_json = client_linkedin_contact.json


#agents facebook info
client_facebook_id='chris.biren'
client_facebook_contact = fbscraper.get_facebook_contact("https://www.facebook.com/" + client_facebook_id, scroll_to_bottom=True)
client_facebook_profile = client_facebook_contact.get_profile_info
client_facebook_location = client_facebook_profile.get("lives_in")
client_facebook_state = client_facebook_location.split(", ")[-1]
client_engagers = client_facebook_contact.get_recent_engagers
client_engagers = fbscraper.get_likers(client_facebook_contact)
client_engagers = client_facebook_contact.top_engagers #75

client_schools = list(set([school.name for school in client_linkedin_contact.schools] + [client_facebook_profile.get("school_name")]))

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

#248
linkedin_friends = set(client_json["email_linkedin_ids"])
#529
facebook_friends = set(client_json["email_facebook_ids"] + client_facebook_contact.get_friends)
client_engagers = facebook_friends & client_engagers #65

valid_locations = ['CO', 'Colorado','Colorado Area','Greater Denver Area', client_facebook_state]
exclusions = [client_facebook_profile.get("job_company"), client_linkedin_contact.current_job.company.name, 'New York Life']


#248
linkedin_contacts = []
for friend in linkedin_friends:
	contact = from_linkedin_id(friend)
	if not contact: 
		print " not found " + friend
		continue
	linkedin_contacts.append(contact)

#529
facebook_contacts = []
for username in facebook_friends:
	contact = fbscraper.get_facebook_contact("https://www.facebook.com/" + username)
	#contact = session.query(FacebookContact).get(username)
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
	linkedin_match = False
	profile_info = facebook_contact.get_profile_info
	facebook_name = profile_info.get("name").lower() if profile_info and profile_info.get("name") else ""
	contact_linkedin_url = get_specific_url(facebook_contact.social_accounts, type="linkedin.com")
	if contact_linkedin_url:  
		linkedin_contact = from_url(contact_linkedin_url)	
		if linkedin_contact:
			print facebook_name + " == " + linkedin_contact.name	
			all_contacts.append((facebook_contact,linkedin_contact))
			matching_linkedin_ids.append(linkedin_contact.linkedin_id)
			linkedin_match = True
			continue
	# if not profile_info: continue
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
			all_contacts.append((facebook_contact,linkedin_contact))
			matching_linkedin_ids.append(linkedin_contact.linkedin_id)
			linkedin_match = True
			break
	if not linkedin_match: 
		all_contacts.append(facebook_contact)
#all_contacts = 529
#matching_linkedin_ids = 160
for linkedin_contact in linkedin_contacts:
	if linkedin_contact.linkedin_id not in matching_linkedin_ids: all_contacts.append(linkedin_contact)
#all_contacts = 646


#46
data_folder = '/Users/lauren/Documents/javascript/' + client_facebook_id + '/js/'
contact_profiles = []
n_valid=0
for contact in all_contacts:
	valid_profile = valid_lead(contact, locales=valid_locations, exclude=exclusions, min_salary=min_salary, schools=client_schools)
	if valid_profile:
		n_valid+=1
		contact_profiles.append(valid_profile)
contact_profiles = compute_stars(contact_profiles)
json.dump(contact_profiles, open(data_folder + 'contact_profiles.json','w'))

p200_schools = {}
for profile in contact_profiles:
	linkedin_url = profile.get("linkedin")
	if not linkedin_url: continue
	p200_prospect = from_url(linkedin_url)
	if not p200_prospect: continue
	for school in p200_prospect.schools:
		if not school.linkedin_school: continue
		name = school.linkedin_school.name
		recs = p200_schools.get(name,[])
		recs.append(profile)
		p200_schools[name] = recs
json.dump(p200_schools,open( data_folder + 'p200_schools.json','w'))

extended_facebook_network = {}
potential_nominators = 0
for username in client_engagers:
	contact = fbscraper.get_facebook_contact("https://www.facebook.com/" + username, scroll_to_bottom=True)
	#if contact.get_profile_info.get("lives_in") and contact.get_profile_info.get("lives_in").split(", ")[-1] not in valid_locations: continue
	if not valid_lead(contact, locales=valid_locations, exclude=exclusions, min_salary=min_salary, schools=client_schools): continue
	potential_nominators +=1
	fbscraper.get_likers(contact)
	engagers = contact.top_engagers
	for engager in engagers:
		if engager in facebook_friends or engager == client_facebook_id or engager == '': continue
		recs = extended_facebook_network.get(engager, [])
		recs.append(contact.facebook_id)
		extended_facebook_network.update({engager: recs})	
	print len(extended_facebook_network)

import joblib
extended_facebook_network = joblib.load('extended_facebook_network')
extended_profiles = []
for username in extended_facebook_network:
	contact = fbscraper.get_facebook_contact("https://www.facebook.com/" + username)
	if not contact: continue
	lead = contact
	contact_linkedin_url = get_specific_url(contact.social_accounts, type="linkedin.com")
	if contact_linkedin_url:  
		contact_linkedin = from_url(contact_linkedin_url)
		if contact_linkedin: lead = (contact,contact_linkedin)
	valid_profile = valid_lead(lead, locales=valid_locations, exclude=exclusions, min_salary=min_salary)
	if valid_profile:
		introducer_username = extended_facebook_network[valid_profile.get("id")]
		introducer_contact = session.query(FacebookContact).get(introducer_username)
		name = introducer_contact.get_profile_info.get("name")
		valid_profile["introducer_url"] = introducer_contact.build_profile.get("url")
		valid_profile["introducer_name"] = name			
		extended_profiles.append(valid_profile)	

extended_profiles = compute_stars(extended_profiles)
json.dump(extended_profiles, open(data_folder + 'extended_profiles.json','w'))

top_nominators = {}
for p in extended_profiles:
	 name = p.get("introducer_name")
	 count = top_nominators.get(name,0) + 1
	 top_nominators[name] = count

import operator
top_nominators = sorted(top_nominators.items(), key=operator.itemgetter(1), reverse=True)