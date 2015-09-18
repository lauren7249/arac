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
	if email_address: 
		by_email.setdefault(email_address,{}).setdefault(service,[]).append(first_name + " " + last_name)
	if first_name and last_name:
		by_name.setdefault(first_name + " " + last_name,{}).setdefault(service,[]).append(email_address)
	#email_domain = email_address.split('@')[-1].lower()
	# bad_contact = (service != 'linkedin' and service!='facebook' and (not first_name or not last_name) and email_domain != 'gmail.com')
	# if bad_contact: print info

labeled = pandas.read_csv("/Users/lauren/Documents/data/lauren_contacts.csv",sep="\t")
labeled.fillna('0',inplace=True)

for index, row in labeled.iterrows():
    by_name[row['name']]['unknown'] = (int(row.unknown)>0)
