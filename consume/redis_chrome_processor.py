from prime.utils import r, profile_re
from services.scraping_helper_service import process_url, process_content, url_to_s3_key
import time, re

while True:
	url = r.spop("chrome_uploads")
	if url and re.search(profile_re,url): 
		fn = url_to_s3_key(url)
		content = process_url(fn)
		id = process_content(content, source_url=url)
		if not id: r.sadd("urls",url)
	else: time.sleep(2)

