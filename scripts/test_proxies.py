from prime.utils.scrape_proxies import r
from consume.proxy_scrape import get, ping, get_ip, add_urls
import datetime
from consume.convert import parse_html
import multiprocessing
from geoip import geolite2
from prime.utils.s3_upload_parsed_html import upload

timeout = 5
n_processes = 500

def work():
	while True:
		raw=r.rpop("untested_promising_proxies")
		if raw is None: break
		d = eval(raw)
		source = d.get("source")
		proxy = d.get("proxy")
		test_url = r.spop("urls")
		d = test_proxy(proxy, test_url=test_url, source=source, d=d)

def test_proxy(proxy, test_url="://www.linkedin.com/pub/annemarie-kunkel/9b/3a/39b", source=None, d={}):
	d.update({"source":source,"proxy":proxy})
	time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	complete_proxy = len(proxy.split(":")) == 3
	if not complete_proxy:
		http_response = get(test_url, "http://" + proxy, timeout=timeout)
		https_response = get(test_url, "https://" + proxy, timeout=timeout)
		response = https_response
		if response is None: response = http_response
	else:
		response = get(test_url, proxy, timeout=timeout)
	defunct = response is None
	d.update({"timeout":timeout,"defunct":defunct, "time_checked":time})
	if defunct: 
		r.rpush("tested_promising_proxies",d)
		return d
	ip = get_ip(proxy)
	match = geolite2.lookup(ip)
	d.update({"country":match.country,"continent":match.continent, "response_code":response.status_code, "response_headers": response.headers})
	if response.status_code != 200:
		r.rpush("tested_promising_proxies",d)
		return d
	info = parse_html(response.content)
	d.update({"redirect": not info.get("success")}) 
	if not info.get("success"):
		d.update({"html": response.content})
		r.rpush("tested_promising_proxies",d)
		return d
	d.update({"incomplete": not info.get("complete")}) 	 
	if not info.get("complete"):
		d.update({"html": response.content})
		r.rpush("tested_promising_proxies",d)
		return d		
	r.rpush("tested_promising_proxies",d)
	r.sadd("good_proxies",proxy)
	upload(info)
	return d

if __name__=="__main__":
	if r.llen("untested_promising_proxies")>r.scard("urls") and False:
		add_urls(filename="/Users/lauren/test_urls.txt", limit=r.llen("untested_promising_proxies"))	
	pool = multiprocessing.Pool(n_processes)
	for i in xrange(0, n_processes):
		pool.apply_async(work, ())
	pool.close()
	pool.join()
