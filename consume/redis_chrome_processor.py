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
import mandrill

facebook_xpaths = [".//img[@class='profilePic img']", ".//span[@id='fb-timeline-cover-name']",".//div[@role='article']"]
mandrill_client = mandrill.Mandrill('AAOgyD72xIgYdntcRNvUvA')

def record_bad(url, user_id):
	n_tries = r.hincrby("bad_urls",url,1)
	user_failures = float(r.hincrby("chrome_uploads_failures",user_id,1))
	user_successes = float(r.hget("chrome_uploads_successes",user_id))
	user_success_rate = float(user_successes)/float(user_successes+user_failures)
	if n_tries<3 or user_success_rate<0.9: r.sadd("urls",url)
	if user_success_rate<0.5 and user_failures==100:
		text = 'User ' + str(user_id) + ' has had ' + str(user_failures) + ' failed urls and ' + str(user_successes) + ' successful urls.' 
		message = {'to':[{'email':'lauren@advisorconnect.co'}],'text':text, 'subject':'Chrome plugin failure', 'from_email':'lauren@advisorconnect.co'}
		try:
			result = mandrill_client.messages.send(message=message, async=False)
		except:
			pass


while True:
	url = r.spop("chrome_uploads")
	if url:
		fn = url_to_s3_key(url)
		user_id = r.hget("chrome_uploads_users",url)
		content = process_url(fn)
		if not content: 
			record_bad(url, user_id)
			continue
		if re.search(profile_re,url): 
			info = parse_html(content)
			if info.get("success") :
				if info.get("complete"):
					info["source_url"] = url
					new_prospect = insert_linkedin_profile(info, session)    			
					if not new_prospect: 
						record_bad(url, user_id)
					else:
						r.hincrby("chrome_uploads_successes",user_id,1)
				else:
					old_prospect = from_url(url)
					if old_prospect and old_prospect.image_url is None and info.get("image"):
						old_prospect.image_url = info.get("image")
						session.add(old_prospect)
						session.commit()
						r.hincrby("chrome_uploads_successes",user_id,1)
					else:
						record_bad(url, user_id)
			else:
				record_bad(url, user_id)
		elif url.find("google.com"):
			if not page_is_good(content, google_xpaths): 
				record_bad(url, user_id)
			else:
				r.hincrby("chrome_uploads_successes",user_id,1)
		elif url.find("facebook.com"):
			if not page_is_good(content, facebook_xpaths): 
				record_bad(url, user_id)
			else:
				r.hincrby("chrome_uploads_successes",user_id,1)
	else: time.sleep(2)

