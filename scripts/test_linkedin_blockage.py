from prime.utils import r
import sys, time
from random import randint
from scripts.test_proxies import try_url
from prime.utils.s3_upload_parsed_html import upload

maxsleep = 10
minsleep = 0
repeat = 1000
total_requests = 0
start_time = time.time()
current_sleep = 0

while True:
	for iteration in xrange(0, repeat):
		url = r.spop("urls")
		info, content = try_url(test_url=url)
		if content is None:
			minutes = (time.time() - start_time)/60
			info.update({"minutes_running":minutes, "total_requests": total_requests,"iteration":iteration, "maxsleep":maxsleep, "minsleep":minsleep,"current_sleep":current_sleep, "repeat":repeat})
			r.rpush("denial", info)
			break
		upload(content)
		r.sadd("completed_urls", url)
		for new_url in content.get("urls"):
			if not r.sismember("completed_urls",new_url): r.sadd("urls", new_url)					
		if maxsleep> minsleep:
			current_sleep = randint(minsleep, maxsleep)
			time.sleep(current_sleep)
		total_requests+=1
	if maxsleep>minsleep: maxsleep-=1