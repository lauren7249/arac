from prime.utils import r
import sys, time
from random import randint
from scripts.test_proxies import try_url
from prime.utils.s3_upload_parsed_html import upload
import requests
import multiprocessing

def work(queue_name = "insight_urls", proxy=None):
	maxsleep = 4
	minsleep = 2
	repeat = 1000
	total_requests = 0
	start_time = time.time()
	current_sleep = 0
	denied = False
	failed_in_a_row = 0
	s = requests.Session()	
	if proxy is not None: r.sadd("in_use_proxies", proxy)
	while not denied:
		for iteration in xrange(0, repeat):
			url = r.srandmember(queue_name)
			if url is None: return
			info, content = try_url(test_url=url, session=s, proxy=proxy)
			if content is None:
				print "failure!"
				r.sadd(queue_name,url)
				failed_in_a_row +=1
				if failed_in_a_row >5: denied = True
				if denied: 
					minutes = (time.time() - start_time)/60
					info.update({"minutes_running":minutes, "total_requests": total_requests,"iteration":iteration, "maxsleep":maxsleep, "minsleep":minsleep,"current_sleep":current_sleep, "repeat":repeat})
					r.rpush("denial", info)		
					if proxy is not None: 
						r.srem("in_use_proxies", proxy)		
						r.sadd("bad_proxies",proxy)
					break
				continue
			failed_in_a_row = 0
			upload(content)
			prospect_id = requests.post("http://54.164.119.139:8080/insert", data=str(content)).content
			if prospect_id: 
				print prospect_id
				r.sadd("completed_urls", url)
				r.srem(queue_name,url)
			for new_url in content.get("urls"):
				if not r.sismember("completed_urls",new_url): r.sadd("urls", new_url)					
			if maxsleep> minsleep:
				current_sleep = randint(minsleep, maxsleep)
				time.sleep(current_sleep)
			total_requests+=1
		if maxsleep>minsleep: maxsleep-=1

if __name__=="__main__":
	n_processes = 999
	urls_queue_name = sys.argv[1]
	proxies_queue_name = sys.argv[2]
	
	pool = multiprocessing.Pool(n_processes)
	while r.scard(proxies_queue_name)>0:
		proxy = r.spop(proxies_queue_name)
		pool.apply_async(work, (), dict(queue_name=urls_queue_name, proxy=proxy))

	pool.close()
	pool.join()