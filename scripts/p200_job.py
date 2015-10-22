from prime.utils import r
from consume.li_scrape_job import scrape_job
from prime.prospects.models import EmailContact, CloudspongeRecord, LeadProfile, get_or_create, session, Agent
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

		agent = session.query(Agent).get(user_email)
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

		client_linkedin_contact = from_url(public_url)
		client_schools = [school.name for school in client_linkedin_contact.schools]
		exclusions = [client_linkedin_contact.current_job.company.name, 'NYLIFE Securities LLC','NYLIFE Securities, LLC','NYLIFE Securities']


		for prospect_id in agent.prospect_ids.keys():
			try:
				prospect = session.query(Prospect).get(prospect_id)
				associated_emails = agent.prospect_ids.get(prospect_id,[])
				valid_profile = valid_lead(prospect, exclude=exclusions, min_salary=35001, schools=client_schools, geopoint=client_geopoint, associated_emails=associated_emails)
				if valid_profile:
					lead = get_or_create(session,LeadProfile,agent_id=agent.email, id=str(valid_profile.get("id")))
					for key, value in valid_profile.iteritems():
					    setattr(lead, key, value)		
					session.add(lead)
					session.commit()
			except:
				continue

		contact_profiles = session.query(LeadProfile).filter(and_(LeadProfile.agent_id==user_email,not_(LeadProfile.extended.is_(True)))).all() 

		extended_urls = set()
		for profile in contact_profiles:
			urls = set(bing.search_extended_network(profile.name, school=profile.company_name) + profile.people_links)
			for url in urls:
				if url not in agent.linkedin_urls.keys(): extended_urls.add(url)

		#1.26 urls/second
		seconds_scraped, urls_scraped = scrape_job(extended_urls,update_interval=10)
		for profile in contact_profiles:		
			if not profile.prospect: continue
			urls = set(bing.search_extended_network(profile.name, school=profile.company_name) + profile.people_links)
			if not profile.friend_prospect_ids:
				friend_prospect_ids = []
				for url in urls:
					if url in agent.linkedin_urls.keys(): continue
					li = from_url(url)
					if not li: continue
					commonality = has_common_institutions(profile.prospect,li)
					if not commonality: continue
					friend_prospect_ids.append(li.id)
				profile.friend_prospect_ids = friend_prospect_ids
				session.add(profile)
				session.commit()
			if not profile.friend_prospect_ids: continue
			for prospect_id in profile.friend_prospect_ids:
				if str(prospect_id) in agent.prospect_ids.keys(): continue
				li = from_prospect_id(prospect_id)
				commonality = has_common_institutions(profile.prospect,li)
				valid_profile = valid_lead(li, exclude=exclusions, min_salary=35001, schools=client_schools, geopoint=client_geopoint)
				if not valid_profile: continue
				extended_lead = get_or_create(session,LeadProfile,agent_id=agent.email, id=str(valid_profile.get("id")))
				for key, value in valid_profile.iteritems():
				    setattr(extended_lead, key, value)	
				extended_lead.referrer_id = profile.id
				extended_lead.referrer_url = profile.url
				extended_lead.referrer_name = profile.name
				extended_lead.referrer_connection = commonality	
				extended_lead.extended = True
				session.add(extended_lead)
				session.commit()		

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


	
