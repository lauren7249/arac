from prime.utils import r
from consume.li_scrape_job import scrape_job
from prime.prospects.models import EmailContact, get_or_create, session
from prime.prospects.lead_model import CloudspongeRecord
from prime.prospects.lead_model import *
from prime.prospects.agent_model import *
from prime.prospects.get_prospect import get_session, from_url
from prime.utils.geocode import *
from prime.utils.networks import *
from prime.utils import bing
from sqlalchemy import and_, not_
from prime.utils.company_info import *
import logging
logger = logging.getLogger()
logger.addHandler(logging.StreamHandler())
from prime.utils import sendgrid_email
import sys, datetime
import traceback

if  __name__=="__main__":
	user_email = sys.argv[1]
	start_time = datetime.datetime.now()
	print "starting"
	try:
		exclusions = ['New York Life Insurance Company','NYLIFE Securities LLC','NYLIFE Securities, LLC','NYLIFE Securities']
		agent = session.query(Agent).get(user_email)
		agent.company_exclusions = exclusions
		session.add(agent)
		session.commit()
		location = agent.geolocation
		public_url = agent.public_url
		client_coords = get_mapquest_coordinates(location).get("latlng")
		client_geopoint = GeoPoint(client_coords[0],client_coords[1])
		print location
		print public_url

		unique_emails = agent.get_email_contacts

		print str(len(unique_emails.keys())) + " unique emails "

		#takes about 30 minutes
		linkedin_urls = agent.get_linkedin_urls

		print str(len(linkedin_urls.keys())) + " linkedin urls "

		#rougly 1 url/second
		seconds_scraped, urls_scraped = scrape_job(linkedin_urls.keys() + [public_url],update_interval=10)

		#1150
		prospect_ids = agent.get_prospect_ids

		contact_profiles = agent.get_qualified_leads

		extended_urls = agent.get_extended_urls

		#1.26 urls/second
		seconds_scraped, urls_scraped = scrape_job(extended_urls,update_interval=10)

		extended_profiles = agent.get_extended_leads

		contact_profiles = session.query(LeadProfile).filter(LeadProfile.agent_id==user_email).all() 
		augment_company_info(contact_profiles)

		for profile in contact_profiles:
			get_phone_number(profile, None)

		agent.refresh_visual

		total_hours = float((datetime.datetime.now() - start_time).seconds)/float(60*60)
		sendgrid_email('lauren@advisorconnect.co','successful p200',user_email + " completed p200 after " + str(total_hours) + " hours" )
	except:
		exc_info = sys.exc_info()
		traceback.print_exception(*exc_info)
		exception_str = traceback.format_exception(*exc_info)
		sendgrid_email('lauren@advisorconnect.co','failed p200',user_email + " failed with error " + str(exception_str))


	
