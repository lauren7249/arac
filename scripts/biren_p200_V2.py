from consume.facebook_friend import *
from prime.prospects.models import *
from prime.prospects.get_prospect import *

contact_profiles = []

refresh = False
min_salary = 55000

#agents facebook info
fbscraper = FacebookFriend()
facebook_id='chris.biren'
facebook_contact = session.query(FacebookContact).get(facebook_id)
if not facebook_contact: facebook_contact = FacebookContact(facebook_id=facebook_id)
facebook_friends = facebook_contact.get_friends
facebook_profile = facebook_contact.get_profile_info
facebook_location = facebook_profile.get("lives_in")
facebook_state = facebook_location.split(", ")[-1]

for username in facebook_friends:
	username = fbscraper.scrape_profile("https://www.facebook.com/" + username)
	#fbscraper.scrape_profile_friends(username)

#agents linkedin info
linkedin_id='103258031' 
prospect = from_linkedin_id(linkedin_id)
prospect_json = prospect.json
linkedin_friends = prospect_json["first_degree_linkedin_ids"]

facebook_linkedin_friends = []

#agents facebook network
for friend in facebook_friends:
	contact = session.query(FacebookContact).get(friend)
	if not contact.linkedin_url: 
		contact.linkedin_url = get_specific_url(contact.social_accounts, type="linkedin.com")
	if contact.linkedin_url:
		contact_linkedin = from_url(contact.linkedin_url)
		if contact_linkedin: facebook_linkedin_friends.append(str(contact_linkedin.linkedin_id))
	
	if valid_lead(contact, locales=[facebook_state], exclude=[facebook_profile.get("job_company")], min_salary=min_salary): 
		profile = contact.build_profile
		contact_profiles.append(profile)

prospect_json["facebook_friend_linkedin_ids"] = facebook_linkedin_friends
prospect.json = prospect_json
session.add(prospect)
session.commit()

linkedin_friends = prospect.json["first_degree_linkedin_ids"]
valid_locations = ['Colorado','Colorado Area','Greater Denver Area']

for friend in linkedin_friends:
	contact = from_linkedin_id(friend)
	if not contact: continue
	contact.get_pipl_response
	if valid_lead(contact, locales=valid_locations, min_salary=min_salary): 
		if refresh: profile = contact.build_profile
		image_url = profile.get("image_url")
		if not image_url: continue
		response = requests.get(image_url, headers=headers)
		if response.status_code == 404: 
			contact.image_url = None
			session.add(contact)
			session.commit()	
			continue
		contact_profiles.append(profile)
	# if str(contact.linkedin_id) not in facebook_linkedin_friends:
	# 	facebook_url = get_specific_url(contact.social_accounts, type="facebook.com")
	# 	if facebook_url:
	# 		print facebook_url

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
	print link
	username = fbscraper.scrape_profile(link)
	print username
	email_facebook_friends.append(username)
	print len(email_facebook_friends)
	#fbscraper.scrape_profile_friends(username)	
email_facebook_friends = list(set(email_facebook_friends))	

prospect_json["email_facebook_ids"] = email_facebook_friends
prospect.json = prospect_json
session.add(prospect)
session.commit()

for linkedin_url in set(email_linkedin_friend_links):
	r.sadd("urls",linkedin_url)

#after scraping
#248
email_linkedin_friends = []
for linkedin_url in set(email_linkedin_friend_links):
	contact_linkedin = from_url(linkedin_url)
	if contact_linkedin: email_linkedin_friends.append(str(contact_linkedin.linkedin_id))

prospect_json["email_linkedin_ids"] = email_linkedin_friends
prospect.json = prospect_json
session.add(prospect)
session.commit()
	#else: r.sadd("urls",linkedin_url)

for linkedin_id in set(prospect_json["email_linkedin_ids"] + prospect_json["facebook_friend_linkedin_ids"] + prospect_json["first_degree_linkedin_ids"]):
	contact = from_linkedin_id(linkedin_id)
	search_query = extended_network_query_string(contact)
	r.sadd("urls",search_query)	
	#search_extended_network(contact)