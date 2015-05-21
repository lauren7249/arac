from prime.utils.scrape_proxies import r
from consume.proxy_scrape import get, ping, get_ip, add_urls
import datetime
from consume.convert import parse_html
import multiprocessing

if r.llen("untested_proxies")>r.scard("urls"):
	add_urls(filename="/Users/lauren/test_urls.txt", limit=r.llen("untested_proxies"))
timeout = 8
n_processes = 1000

def work():
	while True:
		raw=r.rpop("untested_proxies")
		if raw is None: break
		time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		d = eval(raw)
		source = d.get("source")
		proxy = d.get("proxy")
		test_url = r.spop("urls")
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
			r.rpush("tested_proxies",d)
			continue
		ip = get_ip(proxy)
		match = geolite2.lookup(ip)
		d.update({"country":match.country,"continent":match.continent, "response_code":response.status_code, "response_headers": response.headers})
		if response.status_code != 200:
			r.rpush("tested_proxies",d)
			continue
		info = parse_html(response.content)
		d.update({"redirect": not info.get("success")}) 
		if not info.get("success"):
			d.update({"html": response.content})
			r.rpush("tested_proxies",d)
			continue	
		d.update({"incomplete": not info.get("complete")}) 	 
		if not info.get("complete"):
			d.update({"html": response.content})
			r.rpush("tested_proxies",d)
			continue			
		r.rpush("tested_proxies",d)

pool = multiprocessing.Pool(n_processes)
for i in xrange(0, n_processes):
	pool.apply_async(work, ())
pool.close()
pool.join()