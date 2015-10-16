from prime.utils import r
from consume.li_scrape_job import scrape_job
from datetime import datetime
from prime.prospects.models import EmailContact, CloudspongeRecord, get_or_create, session 
from prime.prospects.get_prospect import get_session, from_url
from prime.utils.geocode import *

def email_to_linkedin(email):
	ec = session.query(EmailContact).get(email)
	if not ec: ec = EmailContact(email=email)
	li = ec.get_linkedin_url
	return li

# if  __name__=="__main__":
	
user_email = 'laurentracytalbot@gmail.com'

contacts = session.query(CloudspongeRecord).filter(CloudspongeRecord.user_email==user_email).limit(100).all()

location = contacts[0].geolocation
client_coords = get_mapquest_coordinates(location).get("latlng")
client_geopoint = GeoPoint(client_coords[0],client_coords[1])

unique_emails = set()
for contact in contacts:
	rec = contact.get_emails
	unique_emails.update(rec)
linkedin_urls = set()
for email in unique_emails:
	url = email_to_linkedin(email)
	if url: linkedin_urls.add(url)

seconds_scraped, urls_scraped = scrape_job(linkedin_urls)

linkedin_contacts = []
for url in linkedin_urls:
	contact = from_url(url)
	if not contact: continue
	linkedin_contacts.append(contact)	

