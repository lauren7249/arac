from prime.prospects.models import *
from consume.api_consumer import *
from prime.prospects.get_prospect import *
import datetime
from prime.utils import bing
import pandas
from consume.li_scrape_job import *

li_df = pandas.read_csv("/Users/lauren/Downloads/linkedin_connections_export_microsoft_outlook.csv")
li_df = li_df[["Job Title","Company","E-mail Address","First Name","Middle Name","Last Name"]]
li_df.fillna("",inplace=True)

# linkedin_contacts = session.query(CloudspongeRecord).filter(CloudspongeRecord.user_email=='laurentracytalbot@gmail.com')
# for contact in linkedin_contacts: 
# 	if contact.service and contact.service.lower() == 'linkedin':
# 		contact_email = contact.contact['email'][0]['address']

unique_linkedin_emails = set()
sample_size = 2000

test_df = pandas.DataFrame()
for index, row in li_df.iterrows():
	email = row["E-mail Address"]
	unique_linkedin_emails.add(email)
	test_df = test_df.append(row, ignore_index=True)
	if len(unique_linkedin_emails) == sample_size: break
print len(unique_linkedin_emails) #1044

page_limit=10
bing_api_hits = 0 
job_urls = set()
for index, row in test_df.iterrows():
	name = row["First Name"] + " " + row["Last Name"]
	name = re.sub(r'[^\x00-\x7F]+','', name)
	record = bing.query("", domain="linkedin.com", intitle=re.sub(r" ","%2B",name), page_limit=page_limit)
	bing_api_hits += record.pages
	urls = bing.search_linkedin_by_name(name, page_limit=page_limit, limit=300)
	for url in urls:
		job_urls.add(url)
print bing_api_hits #2189
print len(job_urls) #10881 

seconds_scraped, urls_scraped = scrape_job(job_urls)

#run chrome extension
unique_linkedin_handles_bing = set()
for index, row in test_df.iterrows():
	name = row["First Name"] + " " + row["Last Name"]
	title = row["Job Title"]
	company = row["Company"]
	if title == "" and company == "": continue
	urls = bing.search_linkedin_by_name(name, page_limit=10, limit=300)
	found_match = False
	for url in urls:
		p = from_url(url)
		if not p: continue
		if not p.current_job: 
			li_title=""
			li_company = ""
		else:
			li_title = p.current_job.title
			if not p.current_job.company: li_company = ""
			else: li_company = p.current_job.company.name 
		if title == li_title and company == li_company:
			unique_linkedin_handles_bing.add(url)
			found_match = True
			break
	if not found_match: print name + ", " + title + ", " + company

print len(unique_linkedin_handles_bing) #16

unique_linkedin_handles_clearbit = set()
unique_linkedin_handles_pipl = set()
for email in unique_linkedin_emails:
	email_contact = get_or_create(session, EmailContact, email=email)
	clearbit_response = email_contact.get_clearbit_response
	if clearbit_response: 
		linkedin_handle = clearbit_response.get("linkedin",{}).get("handle")
		if linkedin_handle:
			unique_linkedin_handles_clearbit.add("https://www.linkedin.com/" + linkedin_handle)
	pipl_response = email_contact.get_pipl_response
	if pipl_response:
		linkedin_handle = get_specific_url(email_contact.social_accounts,type='linkedin.com')
		if linkedin_handle:
			unique_linkedin_handles_pipl.add(linkedin_handle.replace("http://","https://"))
print len(unique_linkedin_handles_clearbit) #16 -- 53%
print len(unique_linkedin_handles_pipl) #22 -- 73% 

all_ = [unique_linkedin_handles_pipl,unique_linkedin_handles_bing,unique_linkedin_handles_clearbit]
all_urls = set.union(*all_)
for url in all_urls:
	p = from_url(url)
#run chrome extension -- 12
all_linkedin_ids = set()
for url in all_urls:
	p = from_url(url)
	if not p: continue
	all_linkedin_ids.add(p.linkedin_id)
print len(all_linkedin_ids) #26 

clearbit_and_pipl = [unique_linkedin_handles_clearbit,unique_linkedin_handles_pipl]
clearbit_and_pipl_urls = set.union(*clearbit_and_pipl)
clearbit_and_pipl_linkedin_ids = set()
for url in clearbit_and_pipl_urls:
	p = from_url(url)
	if not p: continue
	clearbit_and_pipl_linkedin_ids.add(p.linkedin_id)
print len(clearbit_and_pipl_linkedin_ids) #24

clearbit_and_bing = [unique_linkedin_handles_clearbit,unique_linkedin_handles_bing]
clearbit_and_bing_urls = set.union(*clearbit_and_bing)
bing_and_clearbit_linkedin_ids = set()
for url in clearbit_and_bing_urls:
	p = from_url(url)
	if not p: continue
	bing_and_clearbit_linkedin_ids.add(p.linkedin_id)
print len(bing_and_clearbit_linkedin_ids) #24

pipl_and_bing = [unique_linkedin_handles_pipl,unique_linkedin_handles_bing]
pipl_and_bing_urls = set.union(*pipl_and_bing)
bing_and_pipl_linkedin_ids = set()
for url in pipl_and_bing_urls:
	p = from_url(url)
	if not p: continue
	bing_and_pipl_linkedin_ids.add(p.linkedin_id)
print len(bing_and_pipl_linkedin_ids) #24














unique_linkedin_handles_bing - unique_linkedin_handles_clearbit #manually checked to ensure they were all my connections

#80% coverage