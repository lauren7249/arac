from prime.utils import *
import requests
from eventlet.timeout import Timeout
import re
import lxml.html
requests.packages.urllib3.disable_warnings()

timeout = 5


def try_request(url, expected_xpath, proxy=None):
	#print url
	if proxy is not None:
		protocol = proxy.split(":")[0]
		proxies = {protocol : proxy}
		url = re.sub(r"^https",protocol, url)
		url = re.sub(r"^http",protocol, url)	
	else: proxies = None

	t = Timeout(timeout*2)
	try:
		response = requests_session.get(url, headers=headers, verify=False, timeout=timeout, proxies=proxies)
	except: 
		#print "timeout exception"
		return False, None
	finally:
		t.cancel()	
	if response.status_code != 200: 
		#print response.status_code 
		return False, response
	raw_html = lxml.html.fromstring(response.content)
	#print response.content
	if len(raw_html.xpath(expected_xpath))==0: return False, response
	return True, response

def robust_get_url(url, expected_xpath):
	successful, response = try_request(url, expected_xpath)
	if successful: return lxml.html.fromstring(response.content)
	potential_proxies = []
	potential_proxies = r.zrangebyscore(good_proxies,0,int(time.time())-wait_seconds)
	while r.scard(good_proxies)>0:
		proxy = r.spop(good_proxies)
		#proxy="https://199.48.185.9:80"
		successful, response = try_request(url, expected_xpath, proxy=proxy)
		if successful: 
			r.sadd(good_proxies,proxy)
			return lxml.html.fromstring(response.content)
		r.sadd(bad_proxies, proxy)
		#break
	return None