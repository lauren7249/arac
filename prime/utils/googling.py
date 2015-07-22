import re
from prime.utils.proxy_scraping import robust_get_url

secret_sauce = "&es_sm=91&ei=NZxTVY_lB8mPyATvpoGACg&sa=N"
def search(querystring, results_per_page=100, start_num=0, limit=1000000, url_regex=".", require_proxy=False):
	urls = set()
	while True:
		search_query ="http://www.google.com/search?q=" + querystring + secret_sauce + "&num=" + str(results_per_page) + "&start=" + str(start_num) 
		print search_query
		raw_html = robust_get_url(search_query, "//*[contains(@class,'srg')]", require_proxy=require_proxy)
		if raw_html is None: break
		results_area = raw_html.xpath("//*[contains(@class,'srg')]")
		links = results_area[0].xpath("//h3[@class='r']/a")
		for linkel in links:
			link = linkel.values()[0]
			if re.search(url_regex,link): urls.add(link)
			if limit == len(urls): return urls
		start_num+=results_per_page
	return urls

def search_with_title(querystring, results_per_page=100, start_num=0, limit=1000000, url_regex=".", require_proxy=False):
	results = {}
	while True:
		search_query ="http://www.google.com/search?q=" + querystring + secret_sauce + "&num=" + str(results_per_page) + "&start=" + str(start_num) 
		raw_html = robust_get_url(search_query, "//*[contains(@class,'srg')]", require_proxy=require_proxy)
		if raw_html is None: break
		results_area = raw_html.xpath("//*[contains(@class,'srg')]")
		links = results_area[0].xpath("//h3[@class='r']/a")
		for linkel in links:
			link = linkel.values()[0]
			if re.search(url_regex,link): 
				title = linkel.text
				results.update({link: title})
			if limit == len(results): return results
		start_num+=results_per_page
	return results

def search_linkedin_profile(terms, limit=10, require_proxy=False):
	profile_re = re.compile('(^https?://www.linkedin.com/pub/((?!dir).)*/.*/.*)|(^https?://www.linkedin.com/in/.*)')
	querystring = "site%3Awww.linkedin.com+" + re.sub(r" ", "+", terms)
	urls = search(querystring, url_regex=profile_re, limit=limit, require_proxy=require_proxy)
	return urls

def search_linkedin_school(terms, limit=1, require_proxy=False):
	profile_re = re.compile('^https://www.linkedin.com/edu/*')
	querystring = "site%3Awww.linkedin.com+" + re.sub(r" ", "+", terms)
	results = search_with_title(querystring, url_regex=profile_re, limit=limit, require_proxy=require_proxy)
	return results

def normalize_school_name(name):
	try:
		u = search_linkedin_school(name)
		title = u.values()[0]
		name = title.split("|")[0].strip()
		return name
	except:
		return None

