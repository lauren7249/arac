import re
from .proxy_scraping import robust_get_url

secret_sauce = "&es_sm=91&ei=NZxTVY_lB8mPyATvpoGACg&sa=N"
def search(querystring, results_per_page=100, start_num=0, limit=1000000, url_regex="."):
	urls = set()
	while True:
		search_query ="http://www.google.com/search?q=" + querystring + secret_sauce + "&num=" + str(results_per_page) + "&start=" + str(start_num) 
		start_num+=results_per_page
		raw_html = robust_get_url(search_query, "//*[contains(@class,'srg')]")
		if raw_html is None: break
		results_area = raw_html.xpath("//*[contains(@class,'srg')]")
		links = results_area[0].xpath("//h3[@class='r']/a")
		for linkel in links:
			link = linkel.values()[0]
			if re.search(url_regex,link): urls.add(link)
			if limit == len(urls): return urls
	return urls

def search_linkedin_profile(terms):
	profile_re = re.compile('(^https?://www.linkedin.com/pub/((?!dir).)*/.*/.*)|(^https?://www.linkedin.com/in/.*)')
	querystring = "site%3Awww.linkedin.com+" + re.sub(r" ", "+", terms)
	urls = search(querystring, url_regex=profile_re, limit=50)
	return urls
