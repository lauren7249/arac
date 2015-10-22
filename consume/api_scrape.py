import multiprocessing
from consume.api_consumer import query_pipl, query_clearbit, get_pipl_social_accounts, get_clearbit_social_accounts, get_specific_url
from prime.prospects.models import get_or_create, EmailContact, session

def email_contacts_linkedin_urls(unique_emails):
	linkedin_urls = []
	for_pipl = []
	for email in unique_emails.keys()[:500]:
		ec = get_or_create(session,EmailContact,email=email)	
		if ec.linkedin_url:
			linkedin_urls.append(email)
			continue
		if not ec.pipl_response or ec.pipl_response.get("@http_status_code")==403:
			for_pipl.append(ec)

	print str(len(linkedin_urls)) + " linkedin urls"
	print str(len(for_pipl)) + " for pipl"

	pool = multiprocessing.Pool(10)
	pipl_responses = pool.map(query_pipl, for_pipl)

	for_clearbit = []
	for i in xrange(0, len(for_pipl)):
		email = for_pipl[i]
		ec = session.query(EmailContact).get(email)
		pipl_response = pipl_responses[i]
		ec.pipl_response = pipl_response
		session.add(ec)
		pipl_social_accounts = get_pipl_social_accounts(pipl_response)
		url = get_specific_url(pipl_social_accounts, type="linkedin.com")
		if url:
			ec.linkedin_url = url
			session.add(ec)
			linkedin_urls.append(ec.linkedin_url)
			continue
        if not ec.clearbit_response:
			for_clearbit.append(email)

	session.commit()

	print str(len(linkedin_urls))+  " linkedin urls"
	print str(len(for_clearbit)) +" for clearbit"

	clearbit_responses = pool.map(query_clearbit, for_clearbit)

	for i in xrange(0, len(for_clearbit)):
		email = for_clearbit[i]
		ec = session.query(EmailContact).get(email)
		clearbit_response = clearbit_responses[i]
		ec.clearbit_response = clearbit_response
		session.add(ec)
		clearbit_social_accounts = get_clearbit_social_accounts(clearbit_response)
		url = get_specific_url(clearbit_social_accounts, type="linkedin.com")
		if url:
			ec.linkedin_url = url
			session.add(ec)
			linkedin_urls.append(ec.linkedin_url)
	session.commit()

	return linkedin_urls


