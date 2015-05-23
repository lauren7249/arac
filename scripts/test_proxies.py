from prime.utils.scrape_proxies import r
from consume.proxy_scrape import get, ping, get_ip, add_urls, queue_url
import datetime
from consume.convert import parse_html
import multiprocessing
from geoip import geolite2
from prime.utils.s3_upload_parsed_html import upload
import lxml.html 
import requests

timeout = 5
n_processes = 500

def work():
	test_results = "tested_promising_proxies"
	while True:
		raw=r.rpop("untested_promising_proxies")
		if raw is None: break
		d = eval(raw)
		source = d.get("source")
		proxy = d.get("proxy")
		test_url = r.spop("urls")
		d, info = try_url(proxy=proxy, test_url=test_url, source=source, d=d)
		r.rpush(test_results,d)
		if info is not None:
			upload(info)
			for new_url in info.get("urls"):
				if not r.sismember("completed_urls"): r.sadd("urls")			

def try_url(test_url="://www.linkedin.com/pub/annemarie-kunkel/9b/3a/39b", proxy=None, source=None, d={}, session=None):
	if proxy is not None:
		d.update({"source":source,"proxy":proxy})
		time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		complete_proxy = len(proxy.split(":")) == 3
		if not complete_proxy:
			http_response = get(test_url, "http://" + proxy, timeout=timeout, session=session)
			https_response = get(test_url, "https://" + proxy, timeout=timeout, session=session)
			response = https_response
			if response is None: response = http_response
		else:
			response = get(test_url, proxy=proxy, timeout=timeout, session=session)
		defunct = response is None
		d.update({"timeout":timeout,"defunct":defunct, "time_checked":time})
		if defunct: 
			return d, None
		ip = get_ip(proxy)
		match = geolite2.lookup(ip)
		d.update({"country":match.country,"continent":match.continent, "response_code":response.status_code, "response_headers": response.headers})
	else:
		response = get(test_url, timeout=timeout)
		d.update(eval(requests.get("http://www.realip.info/api/p/realip.php").content))
	if response.status_code != 200:
		return d, None
	info = parse_html(response.content)
	d.update({"redirect": not info.get("success")}) 
	if not info.get("success"):
		d.update({"html": response.content})
		return d, None
	d.update({"incomplete": not info.get("complete")}) 	 
	if not info.get("complete"):
		d.update({"html": response.content})
		return d, None	
	if proxy is not None:
		r.sadd("good_proxies",proxy)
	return d, info

if __name__=="__main__":
	if r.llen("untested_promising_proxies")>r.scard("urls") and False:
		add_urls(filename="/Users/lauren/test_urls.txt", limit=r.llen("untested_promising_proxies"))	
	pool = multiprocessing.Pool(n_processes)
	for i in xrange(0, n_processes):
		pool.apply_async(work, ())
	pool.close()
	pool.join()
