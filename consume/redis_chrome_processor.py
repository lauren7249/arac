from prime.utils import r
from services.scraping_helper_service import process_url, process_content
import time, re

while True:
	url = r.lpop("chrome_uploads")
	if url: 
		print url
		fn = re.sub("https://","",url)
		fn = re.sub("http://", "", fn)
		fn = re.sub("\/","-",fn) + ".html"
		print fn
		content = process_url(fn)
		id = process_content(content)
		if id: r.srem("urls", url)
	else: time.sleep(2)