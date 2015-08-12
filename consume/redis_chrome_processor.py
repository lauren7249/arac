from prime.utils import r, profile_re
from services.scraping_helper_service import process_url, url_to_s3_key
import time, re
from prime.utils.googling import google_xpaths
from prime.utils.proxy_scraping import page_is_good
import lxml.html
from consume.consumer import parse_html
from prime.prospects.get_prospect import from_url, session
from prime.utils.update_database_from_dict import insert_linkedin_profile
from consume.facebook_consumer import *

facebook_xpaths = [".//img[@class='profilePic img']", ".//span[@id='fb-timeline-cover-name']",".//div[@role='article']"]

def record_bad(url):
	n_tries = r.hincrby("bad_urls",url,1)
	if n_tries<3: r.sadd("urls",url)

while True:
	url = r.spop("chrome_uploads")
	if url:
		fn = url_to_s3_key(url)
		content = process_url(fn)
		if not content: 
			record_bad(url)
			continue
		if re.search(profile_re,url): 
			info = parse_html(content)
			if info.get("success") :
				if info.get("complete"):
					info["source_url"] = url
					new_prospect = insert_linkedin_profile(info, session)    			
					if not new_prospect: record_bad(url)
				else:
					old_prospect = from_url(url)
					if old_prospect and old_prospect.image_url is None and info.get("image"):
						old_prospect.image_url = info.get("image")
						session.add(old_prospect)
						session.commit()
					else:
						record_bad(url)
			else:
				record_bad(url)
		elif url.find("google.com"):
			if not page_is_good(content, google_xpaths): record_bad(url)
		elif url.find("facebook.com"):
			if not page_is_good(content, facebook_xpaths): record_bad(url)
	else: time.sleep(2)

