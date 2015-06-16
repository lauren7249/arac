import requests
import lxml.html
#from . import *
import re
from prime.utils import *
try:
	from consume.proxy_scrape import get
except:
	pass

secret_sauce = "&es_sm=91&ei=NZxTVY_lB8mPyATvpoGACg&sa=N"
def search(querystring, results_per_page=100, start_num=0, limit=1000000, url_regex="."):
	urls = set()
	while True:
		search_query ="http://www.google.com/search?q=" + querystring + secret_sauce + "&num=" + str(results_per_page) + "&start=" + str(start_num) 
		start_num+=results_per_page

		response = requests.get(search_query, headers=headers, verify=False)
		# status = 0
		# while status != 200:
		# 	proxy = r.srandmember("good_proxies")
		# 	response = get(search_query, proxy=proxy)
		# 	if response: status = response.status_code

		raw_html = lxml.html.fromstring(response.content)
		results_area = raw_html.xpath("//*[contains(@class,'srg')]")
		if len(results_area) == 0: break
		links = results_area[0].xpath("//h3[@class='r']/a")
		for linkel in links:
			link = linkel.values()[0]
			if re.search(url_regex,link): urls.add(link)
			if limit == len(urls): return urls
	return urls

def search_linkedin_profile(terms):
	profile_re = re.compile('(^https?://www.linkedin.com/pub/((?!dir).)*/.*/.*)|(^https?://www.linkedin.com/in/.*)')
	query = "site%3Awww.linkedin.com+" + re.sub(r" ", "+", terms)
	urls = search(query, url_regex=profile_re, limit=50)
	return urls
