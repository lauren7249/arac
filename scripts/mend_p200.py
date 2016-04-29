import json
import sys
import os
from prime.utils.email import sendgrid_email
from prime import create_app
from flask.ext.sqlalchemy import SQLAlchemy

app = create_app(os.getenv('AC_CONFIG', 'testing'))
db = SQLAlchemy(app)
session = db.session

#when you think you are done, run this to check for stragglers:
#psql arachnid_prod -U arachnid  
#select user_id, email from users where contacts_from_linkedin=0 and linkedin_login_email is not null and manager_id not in (2, 8, 9, 10) and email not like '%@advisorconnect.co%' and not p200_started;
#select user_id, email from users where unique_contacts_uploaded>0 and manager_id not in (2, 8, 9, 10) and email not like '%@advisorconnect.co%' and not p200_completed;
emails = set(open("emails.txt", "r").read().split("\n"))
if __name__=="__main__":
	from prime.users.models import User
	from prime.managers.models import ManagerProfile
	from prime.processing_service.processing_service import ProcessingService	
	for email in emails:
		email = email.lower().strip()
		if not email:
			continue
		session = db.session
		user = session.query(User).filter_by(email=email).first()
		if not user:
			sendgrid_email("jeff@advisorconnect.co", "this one didnt have an account: {}".format(email),"but i tried to run it manually",from_email="lauren@advisorconnect.co")
			continue
		contacts_array, user = user.refresh_contacts(session=session)
		if user.unique_contacts_uploaded ==0:
			sendgrid_email("jeff@advisorconnect.co", "this one didnt upload any contacts: {}".format(email),"but i tried to run it manually",from_email="lauren@advisorconnect.co")
			continue			
		other_locations = []
		manager = session.query(ManagerProfile).get(user.manager_id)
		client_data = {"first_name":user.first_name,"last_name":user.last_name,"email":user.email,"location":manager.address_2,"url":user.linkedin_url,"hired": True,"suppress_emails":True, "other_locations":[]}
		user.clear_data()
		for client_prospect in user.client_prospects:
		    session.delete(client_prospect)
		user.p200_completed = False
		user.p200_started = False
		user.hiring_screen_started = False
		user.hiring_screen_completed = False
		user.p200_submitted_to_manager = False
		user.p200_approved = False
		user.hired = False
		user.not_hired = False
		user.not_hired_reason = None
		user._statistics = {}
		user._statistics_p200 = {}
		user.all_states = {}
		user.intro_js_seen = False
		session.add(user)
		session.commit()        

		service = ProcessingService({"client_data":client_data, "data":contacts_array})
		service.process()
		user = session.query(User).filter_by(email=email).first()
		body = "contacts uploaded: {}, linkedin uploaded: {}, gmail uploaded: {}, stats: {}, manager: {}, location: {}".format(user.unique_contacts_uploaded, user.contacts_from_linkedin, user.contacts_from_gmail, json.dumps(user.statistics(refresh=True, session=session)), manager.user.email, manager.address_2)
		sendgrid_email("jeff@advisorconnect.co", "Manually run p200 just finished: {}".format(user.email), body, from_email="lauren@advisorconnect.co")