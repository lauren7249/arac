from prime.prospects.models import *
from consume.api_consumer import *

linkedin_contacts = session.query(CloudspongeRecord).filter(CloudspongeRecord.user_email=='laurentracytalbot@gmail.com')

unique_linkedin_emails = set()
unique_linkedin_handles_clearbit = set()
unique_linkedin_handles_pipl = set()
for contact in linkedin_contacts:
	if contact.service and contact.service.lower() == 'linkedin':
		contact_email = contact.contact['email'][0]['address']
		if not contact_email: continue
		unique_linkedin_emails.add(contact_email)
		email_contact = get_or_create(session, EmailContact, email=contact_email)
		clearbit_response = email_contact.get_clearbit_response
		if clearbit_response: 
			linkedin_handle = clearbit_response.get("linkedin",{}).get("handle")
			if linkedin_handle:
				unique_linkedin_handles_clearbit.add(linkedin_handle)
		pipl_response = email_contact.get_pipl_response
		if pipl_response:
			linkedin_handle = get_specific_url(email_contact.social_accounts,type='linkedin.com')
			if linkedin_handle:
				unique_linkedin_handles_pipl.add(linkedin_handle)
		if len(unique_linkedin_emails) == 30: break

print len(unique_linkedin_emails) #30
print len(unique_linkedin_handles_clearbit) #16 -- 53%
print len(unique_linkedin_handles_pipl) #22 -- 73% 

import pandas
li_df = pandas.read_csv("/Users/lauren/Downloads/linkedin_connections_export_microsoft_outlook (1) (1).csv")
test_df = pandas.DataFrame()
for index, row in li_df.iterrows():
	email = row["E-mail Address"]
	if email not in unique_linkedin_emails: continue
	test_df = test_df.append(row, ignore_index=True)

test_df = test_df[["Job Title","Company","E-mail Address","First Name","Middle Name","Last Name"]]
for index, row in test_df.iterrows():
	name = row["First Name"] + " " + row["Last Name"]
	urls = bing.search_linkedin_by_name(name, page_limit=10, limit=300)
	#results = bing.query(row["Job Title"], domain="linkedin.com", intitle=re.sub(r" ","%2B",name), page_limit=10)
