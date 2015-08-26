import re, datetime, requests, json
from prime.prospects.models import BingSearches
from prime.prospects.get_prospect import session
from prime.utils import profile_re
from difflib import SequenceMatcher

#api_key = "xmiHcP6HHtkUtpRk/c6o9XCtuVvbQP3vi4WSKK1pKGg" #jimmy@advisorconnect.co
api_key = "VnjbIn8siy+aS9U2hjEmBgBGyhmiShWaTBARvh8lR1s" #lauren@advisorconnect.co

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

def query(terms, domain="", intitle="", page_limit=1):
	record = session.query(BingSearches).get((terms,domain,intitle))
	if not record: 
		querystring = "https://api.datamarket.azure.com/Bing/SearchWeb/v1/Web?Query=%27"
		#if len(terms): querystring += re.sub(r" ","%20",terms) 
		if len(domain): querystring += "site%3A" + domain + "%20"
		if len(intitle): querystring += "intitle%3A" + intitle 
		querystring += "%27&Adult=%27Strict%27" 
		record = BingSearches(terms=terms, site=domain, intitle=intitle, pages=0, results=[], next_querystring=querystring)
		#print querystring
	#print record.next_querystring
	while record.next_querystring and record.pages<page_limit:
		response = requests.get(record.next_querystring + "&$format=json" , auth=(api_key, api_key))
		raw_results = json.loads(response.content)['d']
		record.results += raw_results.get("results",[])
		record.next_querystring = raw_results.get("__next")
		record.pages+=1
		session.add(record)
		session.commit()
	return record.results

# %27site%3Alinkedin.com%20intitle%3AYesenia%2BMiranda%2Blinkedin%27&Adult=%27Strict%27
def search_linkedin_by_name(name, page_limit=1, limit=10):
	results = query("", domain="linkedin.com", intitle=re.sub(r" ","%2B",name), page_limit=page_limit)
	profiles = filter_results(results, url_regex=profile_re, include_terms_in_title=name)
	return profiles[:limit]


