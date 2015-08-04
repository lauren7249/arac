from prime.utils import r, profile_re
from services.scraping_helper_service import process_url, process_content, url_to_s3_key
import time, re
from prime.utils.googling import google_xpaths
from prime.utils.proxy_scraping import page_is_good
import lxml.html

while True:
	url = r.spop("chrome_uploads")
	if url:
		fn = url_to_s3_key(url)
		content = process_url(fn)
		if re.search(profile_re,url): 
			id = process_content(content, source_url=url)
			if not id: r.sadd("urls",url)
		elif url.find("google.com"):
			if not content or not page_is_good(content, google_xpaths): 
				print url
				r.sadd("urls",url)
	else: time.sleep(2)

