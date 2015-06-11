from prime.utils import r
import sys, time
from random import randint
from scripts.test_proxies import try_url
from prime.utils.s3_upload_parsed_html import upload
import requests

def work(queue_name = "insight_urls", proxy=None):
	maxsleep = 5
	minsleep = 2
	repeat = 1000
	total_requests = 0
	start_time = time.time()
	current_sleep = 0
	denied = False
	failed_in_a_row = 0
	s = requests.Session()	
	while not denied:
		for iteration in xrange(0, repeat):
			url = r.spop(queue_name)
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
					break
				continue
			failed_in_a_row = 0
			upload(content)
			prospect_id = requests.post("http://54.164.119.139:8080/insert", data=str(content)).content
			if prospect_id: 
				print prospect_id
				r.sadd("completed_urls", url)
			for new_url in content.get("urls"):
				if not r.sismember("completed_urls",new_url): r.sadd("urls", new_url)					
			if maxsleep> minsleep:
				current_sleep = randint(minsleep, maxsleep)
				time.sleep(current_sleep)
			total_requests+=1
		if maxsleep>minsleep: maxsleep-=1

if __name__=="__main__":
	print sys.argv[1]
	work(queue_name=sys.argv[1])
