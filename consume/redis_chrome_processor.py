from prime.utils import r, profile_re
from services.scraping_helper_service import process_url, url_to_s3_key
import time, re
from prime.utils.googling import google_xpaths
from prime.utils.proxy_scraping import page_is_good
import lxml.html
from consume.consumer import parse_html
from prime.prospects.get_prospect import from_url, session

while True:
	url = r.spop("chrome_uploads")
	if url:
		fn = url_to_s3_key(url)
		content = process_url(fn)
		if not content: 
			r.sadd("urls",url)
			continue
		if re.search(profile_re,url): 
			info = parse_html(content)
			if info.get("success") :
				if info.get("complete"):
					info["source_url"] = url
					new_prospect = insert_linkedin_profile(info, session)    			
					if not new_prospect: r.sadd("urls",url)
				else:
					r.sadd("urls",url)
			else:
				r.sadd("urls",url)
		elif url.find("google.com"):
			if not page_is_good(content, google_xpaths): 
				r.sadd("urls",url)
	else: time.sleep(2)

