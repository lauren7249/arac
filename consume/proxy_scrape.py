import socket 
import multiprocessing
import redis
import requests
import re
from prime.utils.scrape_proxies import *
from datetime import date
from convert import parse_html
import json
import time 

n_processes = 1000

def ping(proxy):
	socket.setdefaulttimeout(5)
	ip = proxy.split(":")[0]
	port = int(proxy.split(":")[1])
	try: socket.socket().connect((ip,port))
	except: return False
	return True

def add_google_search_proxies(filename="~/clean_proxies.txt"):
	import pandas
	df = pandas.read_csv(filename,sep=" ", header=None, names=["proxy","country","continent"])
	df.drop_duplicates(inplace=True)
	df.fillna("NA", inplace=True)
	proxy_list = list(df.proxy)
	for proxy in proxy_list:
	    r.sadd("proxies","http://" + proxy)
	    r.sadd("proxies","https://" + proxy)

def add_structured_proxies(filename="~/hidemyass_proxies.txt"):
	import pandas
	df = pandas.read_csv(filename,sep=" ", header=None, names=["proxy","protocol"])
	df.drop_duplicates(inplace=True)
	df.fillna("NA", inplace=True)
	for index, row in df.iterrows():
		r.sadd("proxies",row["protocol"].lower() + "://" + row["proxy"])

def add_all_proxies():
	add_google_search_proxies()
	add_structured_proxies()
	n_proxies = r.scard("proxies")
	return n_proxies

def queue_url(url):
	if r.hexists("downloaded_urls_hash",url): return 
	url = re.sub("http","", url)
	if r.sismember("urls",url): return
	r.sadd("urls",url)	

def add_urls(filename="/dev/finished_oct30.txt", limit=None):	
	urls = open(filename,"rb")
	for url in urls:
		if r.scard("urls")==limit: break
		url = url.strip()
		queue_url(url)
	urls.close()
	return r.scard("urls")

def get(url, proxy, timeout=8):
	protocol = proxy.split(":")[0]
	proxies = {protocol : proxy}
	link = protocol + url	
	try:
		response = requests.get(link, headers=headers, verify=False, proxies=proxies, timeout=timeout)
	except:
		return None
	return response	

def process_next_url(url):
	proxy = r.srandmember("proxies")
	if proxy is None: 
		r.sadd("urls",url)
		return False
	response = get(url, proxy)	

	if response is not None and response.status_code == 999:
		r.sadd("blacklist_proxies",proxy)
	if response is None or response.status_code == 999:
		r.sadd("urls",url)
		r.srem("proxies",proxy)
		return True	
	try:		
		parsed = parse_html(response.content)
		if not parsed.get("success"): raise BreakoutException
	except:
		r.sadd("blacklist_proxies",proxy)
		r.sadd("urls",url)		
		r.srem("proxies",proxy)
		return True				

	#put the url on the q for processing
	http_link = "http" + url
	r.sadd("downloaded_urls",http_link)
	r.hset("downloaded_urls_hash",http_link, json.dumps(parsed))

	for new_url in parsed.get("urls"):
		queue_url(new_url)

	return True


def work():
	url = r.spop("urls")
	while url is not None:
		http_link = "http" + url
		#skip urls that have already been downloaded
		if r.hexists("downloaded_urls_hash",http_link): continue
		rc = process_next_url(url)
		if not rc:
			for site in sites:
				#fuck. last time we already tried getting more proxies and still no progress!
				if int(r.get("previous_downloaded_urls")) == r.hlen("downloaded_urls_hash") and r.get(site + "_proxies_jobs") is not None:
					return False
				#i am the chosen worker to find more proxies!!!!
				if r.get(site + "_proxies_rescrape") == 'False' or r.get(site + "_proxies_rescrape") is None:
					#tells other workers not to do the proxy rescrape
					r.set(site + "_proxies_rescrape", 'True')
					#mark how many urls are still on the queue 
					r.set("previous_downloaded_urls",r.hlen("downloaded_urls_hash"))
					print "getting more " + site + " proxies"
					get_proxies(redis=r, site=site)
					#keep track of how many times we hit up this website
					r.incr(site + "_proxies_jobs")
					#release status for other workers
					r.set(site + "_proxies_rescrape", 'False')
		url = r.spop("urls")
	return True

if __name__=="__main__":
	for site in sites:
		r.set(site + "_proxies_rescrape", 'False')
		r.set("previous_downloaded_urls",'0')
	pool = multiprocessing.Pool(n_processes)
	for i in xrange(0, n_processes):
		pool.apply_async(work, ())
	pool.close()
	pool.join()
	

