from prime.prospects.models import *
import re

email = 'laurentracytalbot@gmail.com'
contacts = session.query(CloudspongeRecord).filter(CloudspongeRecord.user_email==email).all()
by_name = {}
by_email = {}	
for contact in contacts:
	info = contact.contact 
	service = contact.service.lower()
	first_name = re.sub('[^a-z]','',info.get("first_name","").lower())
	last_name = re.sub('[^a-z]','',info.get("last_name","").lower().replace('[^a-z ]',''))
	emails = info.get("email",[{}])
	try: email_address = emails[0].get("address",'').lower()
	except: email_address = ''