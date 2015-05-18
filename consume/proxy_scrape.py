import pandas
import socket 
import multiprocessing
import redis
import requests
import re
from scrape_proxies import *
from datetime import date
from convert import parse_html
import json
import time 

ua='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
headers ={'User-Agent':ua}
n_processes = 1000

def ping(proxy):
	socket.setdefaulttimeout(5)
	ip = proxy.split(":")[0]
	port = int(proxy.split(":")[1])
	try: socket.socket().connect((ip,port))
	except: return False
	return True

def get_redis(flush=False):
	pool = redis.ConnectionPool(host='processing-001.h1wlwz.0001.use1.cache.amazonaws.com', port=6379, db=0)
	r = redis.Redis(connection_pool=pool)
	if flush: r.flushall()
	return r

def add_google_search_proxies(filename="~/clean_proxies.txt"):
	df = pandas.read_csv(filename,sep=" ", header=None, names=["proxy","country","continent"])
	df.drop_duplicates(inplace=True)
	df.fillna("NA", inplace=True)
	proxy_list = list(df.proxy)
	for proxy in proxy_list:
	    r.sadd("proxies","http://" + proxy)
	    r.sadd("proxies","https://" + proxy)

def add_structured_proxies(filename="~/hidemyass_proxies.txt"):
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
	count=0
	for url in urls:
		url = url.strip()
		queue_url(url)
		count+=1
		if count==limit: break
	urls.close()
	return r.scard("urls")

def get(url, proxy):
	protocol = proxy.split(":")[0]
	proxies = {protocol : proxy}
	link = protocol + url	
	try:
		response = requests.get(link, headers=headers, verify=False, proxies=proxies, timeout=5)
	except:
		return None
	return response	

def process_next_url(url):
	proxy = r.srandmember("proxies")
	if proxy is None: 
		r.sadd("urls",url)
		return False
	response = get(url, proxy)	

	if response.status_code == 999:
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
			#fuck. last time we already tried getting more proxies and still no progress!
			if int(r.get("previous_downloaded_urls")) == r.hlen("downloaded_urls_hash") and r.get("hidemyass_proxies_jobs") is not None:
				return False
			#i am the chosen worker to find more proxies!!!!
			if r.get("hidemyass_proxies_rescrape") == 'False' or r.get("hidemyass_proxies_rescrape") is None:
				#tells other workers not to do the proxy rescrape
				r.set("hidemyass_proxies_rescrape", 'True')
				#mark how many urls are still on the queue 
				r.set("previous_downloaded_urls",r.hlen("downloaded_urls_hash"))
				print "getting more proxies"
				get_hidemyass_proxies(redis=r)
				#keep track of how many times we hit up this website
				r.incr("hidemyass_proxies_jobs")
				#release status for other workers
				r.set("hidemyass_proxies_rescrape", 'False')
			else: 
				#i am waiting for there to be more proxies.
				while r.scard("proxies") == 0 and r.get("hidemyass_proxies_rescrape") == 'True':
					time.sleep(1)
		url = r.spop("urls")
	return True

r = get_redis() 

if __name__=="__main__":
	r.set("hidemyass_proxies_rescrape", 'False')
	r.set("previous_downloaded_urls",'0')
	pool = multiprocessing.Pool(n_processes)
	for i in xrange(0, n_processes):
		pool.apply_async(work, ())
	pool.close()
	pool.join()
	

