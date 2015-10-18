from prime.utils import r
from consume.li_scrape_job import scrape_job
from datetime import datetime
from prime.prospects.models import EmailContact, CloudspongeRecord, get_or_create, session, Agent
from prime.prospects.get_prospect import get_session, from_url
from prime.utils.geocode import *

def email_to_linkedin(email):
	ec = session.query(EmailContact).get(email)
	if not ec: ec = EmailContact(email=email)
	li = ec.get_linkedin_url
	return li

# if  __name__=="__main__":
	
user_email = 'laurentracytalbot@gmail.com'
agent = session.query(Agent).get(user_email)
email_contacts_from_email = agent.email_contacts_from_email if agent.email_contacts_from_email else {}
email_contacts_from_linkedin = agent.email_contacts_from_linkedin if agent.email_contacts_from_linkedin else {}

contacts = session.query(CloudspongeRecord).filter(CloudspongeRecord.user_email==user_email).all() 

location = agent.geolocation
public_url = agent.public_url
client_coords = get_mapquest_coordinates(location).get("latlng")
client_geopoint = GeoPoint(client_coords[0],client_coords[1])

unique_emails = {}
for contact in contacts:
	service = contact.service
	rec = contact.get_emails
	for email in rec:
		domain = email.split("@")[-1].lower().strip()
		if domain in ['docs.google.com'] or domain.find('craigslist.org')>-1 or re.search('(\.|^)reply(\.|$)',domain): 
			print email
			continue
		info = unique_emails.get(email,{})
		sources = info.get("sources",set())
		if service.lower()=='linkedin':
			sources.add('linkedin')
		elif service.lower()=='csv':
			sources.add('csv')
		else:
			source = contact.contacts_owner.get("email",[{}])[0].get("address")
			if source: sources.add(source)
		info["sources"] = sources
		unique_emails[email] = info 

#2533 emails to try
#1347 linkedin urls
linkedin_urls = set()
for email in unique_emails.keys():
	info = unique_emails.get(email,{})
	sources = info.get("sources",set())	
	try:
		url = email_to_linkedin(email)
	except:
		continue
	if url: 
		linkedin_urls.add(url)
		info["linkedin"] = url
	if 'linkedin' in sources: 
		email_contacts_from_linkedin.update({email: info})
	else:
		email_contacts_from_email.update({email: info})
	unique_emails[email] = info 

linkedin_urls.add(public_url)
seconds_scraped, urls_scraped = scrape_job(linkedin_urls)

linkedin_contacts = []
for url in linkedin_urls:
	contact = from_url(url)
	if not contact: continue
	linkedin_contacts.append(contact)	

client_linkedin_contact = from_url(public_url)
client_schools = [school.name for school in client_linkedin_contact.schools]
exclusions = [client_linkedin_contact.current_job.company.name, 'NYLIFE Securities LLC','NYLIFE Securities, LLC','NYLIFE Securities']

contact_profiles = []
n_valid=0
for contact in all_contacts:
	valid_profile = valid_lead(contact, exclude=exclusions, min_salary=35001, schools=client_schools, geopoint=client_geopoint)
	if valid_profile:
		n_valid+=1
		contact_profiles.append(valid_profile)
