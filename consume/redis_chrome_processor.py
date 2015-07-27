from prime.utils import r
from services.scraping_helper_service import process_url, process_content, url_to_s3_key
import time, re

while True:
	url = r.lpop("chrome_uploads")
	if url: 
		fn = url_to_s3_key(url)
		content = process_url(fn)
		id = process_content(content, source_url=url)
		if id: r.srem("urls", url)
	else: time.sleep(2)