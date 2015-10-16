from prime.prospects.models import *
from sqlalchemy import and_, or_
import datetime, time
from prime.utils import r
import sendgrid
 #days

def query_prospects(job_urls):
	job_urls_http = [url.replace("https://","http://") for url in job_urls]
	job_urls_https = [url.replace("http://","https://") for url in job_urls]
	recs = session.query(ProspectUrl.linkedin_id).filter(and_(ProspectUrl.url.in_(list(job_urls)), ProspectUrl.linkedin_id != 1)).distinct().all()
	lids = [rec[0] for rec in recs]
	recs = session.query(Prospect).filter(or_(Prospect.linkedin_id.in_(lids), Prospect.url.in_(job_urls_https), Prospect.url.in_(job_urls_http))).all()
	return recs

def scrape_job(job_urls, update_interval = None):
	
	print str(len(job_urls)) + " job urls"

	if update_interval:
		refresh_date = start_time + datetime.timedelta(-update_interval)

		job_urls_http = [url.replace("https://","http://") for url in job_urls]
		job_urls_https = [url.replace("http://","https://") for url in job_urls]

		recs = session.query(ProspectUrl.linkedin_id).filter(and_(ProspectUrl.url.in_(list(job_urls)), ProspectUrl.linkedin_id != 1)).distinct().all()
		lids = [rec[0] for rec in recs]
	 	print str(len(lids)) + " matching lids from prospecturl table"

		recs = session.query(Prospect).filter(and_(Prospect.updated > refresh_date, or_(Prospect.linkedin_id.in_(lids), Prospect.url.in_(job_urls_https), Prospect.url.in_(job_urls_http)))).add_columns(Prospect.url, Prospect.linkedin_id).all()
		print str(len(recs)) + " recs from prospect table"

		updated_urls_http = [rec.url.replace("https://","http://") for rec in recs]
		updated_urls_https = [rec.url.replace("http://","https://") for rec in recs]
		updated_urls_lids = [rec.linkedin_id for rec in recs]
		recs = session.query(ProspectUrl.url).filter(ProspectUrl.linkedin_id.in_(updated_urls_lids)).distinct().all()
		print str(len(recs)) + " urls from prospecturl table"

		updated_urls = [rec[0] for rec in recs]

		new_urls = job_urls - set(updated_urls_http) - set(updated_urls_https) - set(updated_urls)
	else: 
		new_urls = set(job_urls)

	gmail_user = 'contacts@advisorconnect.co'
	gmail_pwd = '1250downllc'
	sg = sendgrid.SendGridClient('lauren7249',gmail_pwd)
	mail = sendgrid.Mail()
	mail.add_to('lauren@advisorconnect.co')
	mail.set_subject('Scrape job in progress')
	mail.set_text(str(len(new_urls)) + ' urls need to be scraped. Please run the chrome plugin. ')
	mail.set_from(gmail_user)
	status, msg = sg.send(mail)	

	print str(len(new_urls)) + " incremental urls to scrape! adding to queue"
	r.sadd("urls",*new_urls)

	start_time = datetime.datetime.now()

	left_to_scrape = len(r.smembers("urls") & new_urls)
	while(left_to_scrape>5):
		print str(left_to_scrape) + " left to scrape"
		time.sleep(5)
		left_to_scrape = len(r.smembers("urls") & new_urls)

	total_seconds = (datetime.datetime.now() - start_time).seconds
	return total_seconds, len(new_urls)
