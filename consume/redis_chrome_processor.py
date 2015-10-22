from prime.utils import r, profile_re, company_re
from services.scraping_helper_service import process_url, url_to_s3_key, get_user_success_rate, get_user_successes, get_user_failures
import time, re
from prime.utils.googling import google_xpaths
from prime.utils.proxy_scraping import page_is_good
import lxml.html
from consume.convert import parse_html, parse_company
from prime.prospects.get_prospect import from_url, session
from prime.utils.update_database_from_dict import insert_linkedin_profile, insert_linkedin_company
from consume.facebook_consumer import *
import sendgrid
import datetime

facebook_xpaths = [".//img[@class='profilePic img']", ".//span[@id='fb-timeline-cover-name']",".//div[@role='article']"]
gmail_user = 'contacts@advisorconnect.co'
gmail_pwd = '1250downllc'
sg = sendgrid.SendGridClient('lauren7249',gmail_pwd)

def send_alert(id, failures, successes):
	last_sent_timestring = r.hget("email_alert",id)
	now_time = datetime.datetime.utcnow()
	if last_sent_timestring:
		last_sent = datetime.datetime.strptime(last_sent_timestring.split(".")[0],'%Y-%m-%d %H:%M:%S')
		timedelta = now_time - last_sent
		if timedelta.seconds < 60*60: return
	mail = sendgrid.Mail()
	mail.add_to('lauren@advisorconnect.co')
	mail.set_subject('Chrome plugin failure')
	mail.set_text('User ' + str(id) + ' has had ' + str(failures) + ' failed urls and ' + str(successes) + ' successful urls.')
	mail.set_from(gmail_user)
	status, msg = sg.send(mail)	
	r.hset("email_alert", id, now_time)

def record_bad(url, user_id, ip, incomplete=False):
	if not incomplete:
		n_tries = r.hincrby("bad_urls",url,1)
		if n_tries>=3: return
	else:
		n_tries = r.hget("bad_urls",url)
	r.hset("last_failure", user_id, datetime.datetime.utcnow())
	ip_success_rate = get_user_success_rate(ip)
	user_success_rate = get_user_success_rate(user_id)
	ip_failures = get_user_failures(ip)
	user_failures = get_user_failures(user_id)
	if n_tries<3 or user_success_rate<0.9 or ip_success_rate<0.9: r.sadd("urls",url)
	if ip_success_rate<=0.5 and ip_failures>=100:
		send_alert(ip, ip_failures, ip_successes)
	if user_success_rate<=0.5 and user_failures>=100:
		send_alert(user_id, user_failures, user_successes)

if __name__=="__main__":
	while True:
		try:
			url = r.spop("chrome_uploads")
			if url:
				fn = url_to_s3_key(url)
				user_id = r.hget("chrome_uploads_users",url)
				ip = r.hget("chrome_uploads_ips",url)
				content = process_url(fn)
				if not content: 
					record_bad(url, user_id, ip)
					continue
				if re.search(profile_re,url): 
					info = parse_html(content)
					if info.get("success") :
						if info.get("complete"):
							info["source_url"] = url
							new_prospect = insert_linkedin_profile(info, session)    			
							if not new_prospect: 
								record_bad(url, user_id, ip)
							else:
								r.hincrby("chrome_uploads_successes",user_id,1)
								r.hincrby("chrome_uploads_successes",ip,1)
						else:
							old_prospect = from_url(url)
							if old_prospect and old_prospect.image_url is None and info.get("image"):
								old_prospect.image_url = info.get("image")
								session.add(old_prospect)
								session.commit()
								r.hincrby("chrome_uploads_successes",user_id,1)
								r.hincrby("chrome_uploads_successes",ip,1)
							else:
								record_bad(url, user_id, ip, incomplete=True)
					else:
						record_bad(url, user_id, ip)
				elif re.search(company_re,url): 
					info = parse_company(content)
					if info and info.get("id") :
						info["source_url"] = url
						company_id = insert_linkedin_company(info, session)    			
						if not company_id: 
							record_bad(url, user_id, ip)
						else:
							r.hincrby("chrome_uploads_successes",user_id,1)
							r.hincrby("chrome_uploads_successes",ip,1)
					else:
						record_bad(url, user_id, ip)				
				elif url.find("google.com"):
					if not page_is_good(content, google_xpaths): 
						record_bad(url, user_id, ip)
					else:
						r.hincrby("chrome_uploads_successes",user_id,1)
						r.hincrby("chrome_uploads_successes",ip,1)
				elif url.find("facebook.com"):
					if not page_is_good(content, facebook_xpaths): 
						record_bad(url, user_id, ip)
					else:
						r.hincrby("chrome_uploads_successes",user_id,1)
						r.hincrby("chrome_uploads_successes",ip,1)
			else: time.sleep(2)
		except:
			pass
