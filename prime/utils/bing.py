import re, datetime, requests, json
from prime.prospects.models import BingSearches
from prime.prospects.get_prospect import session
from prime.utils import profile_re, school_re, company_re
from difflib import SequenceMatcher

#api_key = "xmiHcP6HHtkUtpRk/c6o9XCtuVvbQP3vi4WSKK1pKGg" #jimmy@advisorconnect.co
#api_key = "VnjbIn8siy+aS9U2hjEmBgBGyhmiShWaTBARvh8lR1s" #lauren@advisorconnect.co
#api_key = "ETjsWwqMuHtuwV0366GtgJEt57BkFPbhnV4oT8lcfgU" #laurentracytalbot@gmail.com
#api_key = "CAkR9NrxB+9brLGVtRotua6LzxC/nZKqKuclWf9GjKU" #lauren.tracy.talbot@gmail.com
#api_key = "hysOYscBLj0xtRDUst5wJLj2vWLyiueCDof6wGYD5Ls" #lauren.tracytalbot@gmail.com
#api_key = "FWyMRXjzB9NT1GXTFGxIdS0JdG3UsGHS9okxGx7mKZ0" #laurentracy.talbot@gmail.com
#api_key = "U7ObwzZDTxyaTPbqwDkhPJ2wy+XfgMuVJ7k2BR/8HcE" #la.urentracytalbot@gmail.com
api_key = "VzTO15crpGKTYwkA8qqRThohTliVQTznqphD+WA5eVA" #l.aurentracytalbot@gmail.com

def filter_results(results, limit=100, url_regex=".", exclude_terms_from_title=None, include_terms_in_title=None):
	filtered = []
	if exclude_terms_from_title: exclude_terms_from_title = exclude_terms_from_title.lower().strip()
	if include_terms_in_title: include_terms_in_title = include_terms_in_title.lower().strip()
	for result in results:
		link = result.get("Url")
		if re.search(url_regex,link): 
			title = result.get("Title")
			title_meat = title.split("|")[0].lower().strip()
			if exclude_terms_from_title:
				ratio = SequenceMatcher(None, title_meat, exclude_terms_from_title.lower().strip()).ratio()
				intersect = set(exclude_terms_from_title.split(" ")) & set(title_meat.split(" "))
				if len(intersect) >= 2 or ratio>=0.8: 
					continue 
			if include_terms_in_title:
				ratio = SequenceMatcher(None, title_meat, include_terms_in_title.lower().strip()).ratio()
				intersect = set(include_terms_in_title.split(" ")) & set(title_meat.split(" "))
				if len(intersect) < 2 and ratio<0.8: 
					continue 					
			filtered.append(link)
		if limit == len(filtered): return filtered
	return filtered

def query(terms, site="", intitle="", inbody=[], page_limit=1):
	record = session.query(BingSearches).get((terms,site,intitle," ".join(inbody)))
	if not record: 
		querystring = "https://api.datamarket.azure.com/Bing/SearchWeb/v1/Web?Query=%27"
		if len(terms): querystring += re.sub(r" ","%20",terms) 
		if len(site): querystring += "site%3A" + site + "%20"
		if len(inbody): 
			for ib in inbody:
				querystring += "inbody%3A" + ib + "%20"
		if len(intitle): querystring += "intitle%3A" + intitle + "%20"
		querystring += "%27&Adult=%27Strict%27" 
		record = BingSearches(terms=terms, site=site, intitle=intitle, inbody=" ".join(inbody), pages=0, results=[], next_querystring=querystring)
		#print querystring
	#print record.next_querystring
	while record.next_querystring and record.pages<page_limit:
		response = requests.get(record.next_querystring + "&$format=json" , auth=(api_key, api_key))
		try:
			raw_results = json.loads(response.content)['d']
			record.results += raw_results.get("results",[])
			record.next_querystring = raw_results.get("__next")		
			record.pages+=1	
			session.add(record)
			session.commit()			
		except:
			print response.content
			break
	return record

# %27site%3Alinkedin.com%20intitle%3AYesenia%2BMiranda%2Blinkedin%27&Adult=%27Strict%27
def search_linkedin_by_name(name, school='', page_limit=1, limit=10):
	if len(school): inbody = '%22' + re.sub(r" ", "%20",school).replace('&','') + '%22' 
	else: inbody = ''
	record = query("", site="linkedin.com", intitle=re.sub(r" ","%2B",name), inbody=[inbody], page_limit=page_limit)
	profiles = filter_results(record.results, url_regex=profile_re, include_terms_in_title=name)
	return profiles[:limit]

def search_extended_network(name, school='', page_limit=22):
	inbody_name = '%22' + re.sub(r" ", "%20",name) + '%22'
	if len(school): 
		inbody_school = '%22' + re.sub(r" ", "%20",school).replace('&','') + '%22'
		inbody = [inbody_name, inbody_school]
	else: inbody = [inbody_name]
	record = query("", site="linkedin.com", inbody=inbody, intitle="%22|%20LinkedIn%22", page_limit=page_limit)
	profiles = filter_results(record.results, url_regex=profile_re, exclude_terms_from_title=name)
	return profiles

def search_linkedin_schools(school):
	record = query("", site="linkedin.com", intitle=re.sub(r" ","%2B",school).replace('&',''), page_limit=22)
	profiles = filter_results(record.results, url_regex=school_re, include_terms_in_title=school)
	school_ids = []
	for link in profiles:
		school_id = re.search("(?<=(\=|\-))[0-9]+", link)
		if not school_id: continue
		school_id = school_id.group(0)
		if school_id not in school_ids: school_ids.append(school_id) 
	return school_ids

def search_linkedin_companies(company):
	record = query("", site="linkedin.com", intitle=re.sub(r" ","%2B",company).replace('&',''), page_limit=22)
	profiles = filter_results(record.results, url_regex=company_re, include_terms_in_title=company)
	urls = []
	for link in profiles:
		id = re.search('^https://www.linkedin.com/company/[a-zA-Z0-9\-]+(?=/)',link)
		if not id:
			if link not in urls: urls.append(link)
			continue
		id = id.group(0)
		if id not in urls: urls.append(id)
	return urls

