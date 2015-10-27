from prime.utils import *
import requests
from eventlet.timeout import Timeout
import re
import lxml.html
from prime.prospects.get_prospect import session
from prime.prospects.models import Proxy, ProxyDomainStatus, ProxyDomainEvent
from datetime import datetime, timedelta
from sqlalchemy import *
from random import randint
from sqlalchemy.orm import joinedload
from services.scraping_helper_service import process_url, process_content, url_to_s3_key

requests.packages.urllib3.disable_warnings()

timeout = 5
try_again_after_timeout_days = 2
max_consecutive_timeouts = 3
try_again_after_reject_days = 1
min_wait_btwn_requests_seconds = 15
max_wait_btwn_requests_seconds = 45
# CONSTANTS
############
DB_USER = 'arachnid'
DB_PASS = 'devious8ob8'

def try_request(url, expected_xpaths, proxy=None):
	#print url
	if proxy is not None:
		protocol = proxy.split(":")[0]
		proxies = {protocol : proxy}
		url = re.sub(r"^https",protocol, url)
		url = re.sub(r"^http",protocol, url)	
	else: proxies = None

	t = Timeout(timeout*2)
	try:
		response = requests.get(url, headers=headers, verify=False, timeout=timeout, proxies=proxies)
	except: 
		#print "timeout exception"
		return False, None
	finally:
		t.cancel()	
	if response.status_code != 200: return False, response
	if page_is_good(response.content, expected_xpaths): return True, response
	return False, response
	
def page_is_good(content, expected_xpaths):
	try:
		raw_html = lxml.html.fromstring(content)
	except:
		return False
	for expected_xpath in expected_xpaths:
		if len(raw_html.xpath(expected_xpath)) > 0: return True
	return False

def get_domain(url):
	url = re.sub(r"^https://","", url)
	url = re.sub(r"^http://","", url)	
	url = re.sub(r"^www.","", url)	
	return url.split("/")[0]

def record_failure(proxy, domain, response):
	now = datetime.utcnow()
	status = session.query(ProxyDomainStatus).get((proxy.url,domain))
	status.in_use=False
	if response is None:
		proxy.last_timeout = now
		proxy.consecutive_timeouts+=1
		event = ProxyDomainEvent(proxy_url=proxy.url, domain=domain, event_time=now, success=False)
	else:
		proxy.last_success = now
		proxy.consecutive_timeouts=0
		status.last_rejected = now
		event = ProxyDomainEvent(proxy_url=proxy.url, domain=domain, event_time=now, status_code=response.status_code, success=False)
	session.add(status)	
	session.add(proxy)	
	session.add(event)
	session.commit()

def record_success(proxy, domain):
	now = datetime.utcnow()
	proxy.last_success = now
	proxy.consecutive_timeouts=0
	session.add(proxy)
	status = session.query(ProxyDomainStatus).get((proxy.url,domain))
	status.last_accepted = now
	status.in_use=False
	event = ProxyDomainEvent(proxy_url=proxy.url, domain=domain, event_time=now, status_code="200", success=True)
	session.add(status)	
	session.add(event)
	session.commit()

#return Proxy object
def proc_pick_proxy(domain):
	#keep wait time random
	wait_btwn_requests_seconds = randint(min_wait_btwn_requests_seconds, max_wait_btwn_requests_seconds)
	last_rejected_threshold1 = datetime.utcnow() - timedelta(days=try_again_after_reject_days)
	last_rejected_threshold2 = datetime.utcnow() - timedelta(seconds=wait_btwn_requests_seconds)
	last_rejected_threshold = min(last_rejected_threshold1, last_rejected_threshold2)
	last_accepted_threshold = datetime.utcnow() - timedelta(seconds=wait_btwn_requests_seconds)
	timeout_threshold = datetime.utcnow() - timedelta(days=try_again_after_timeout_days)
	t = text("select * from get_proxy('" + domain + "', '" +  last_rejected_threshold.strftime('%Y-%m-%d %H:%M:%S') + "', '" + last_accepted_threshold.strftime('%Y-%m-%d %H:%M:%S') + "', '" +  timeout_threshold.strftime('%Y-%m-%d %H:%M:%S') + "')")
	result = session.execute(t)
	
	for r in result:
		proxy_url = r[0]
		break
	if not proxy_url: return None
	# with db() as d:  # This syntax safely returns the connection to the pool upon completion or failure
	# 	cursor = db.raw_connection().cursor()  # Grab a psycopg2 cursor, sqlalchemy doesn't do stored procs
        
 #        # Call the get_proxy() proc with a tuple of parameters passed in and then fetch the result
	# 	cursor.callproc('get_proxy',(domain,last_rejected_threshold,last_accepted_threshold, timeout_threshold))
	# 	proxy_url = cursor.fetchone()	
	proxy = session.query(Proxy).get(proxy_url)
	session.commit()
	#session.close()
	return proxy

#return Proxy object
def pick_proxy(domain):
	#keep wait time random
	wait_btwn_requests_seconds = randint(min_wait_btwn_requests_seconds, max_wait_btwn_requests_seconds)
	last_rejected_threshold1 = datetime.utcnow() - timedelta(days=try_again_after_reject_days)
	last_rejected_threshold2 = datetime.utcnow() - timedelta(seconds=wait_btwn_requests_seconds)
	last_rejected_threshold = min(last_rejected_threshold1, last_rejected_threshold2)
	last_accepted_threshold = datetime.utcnow() - timedelta(seconds=wait_btwn_requests_seconds)
	timeout_threshold = datetime.utcnow() - timedelta(days=try_again_after_timeout_days)
	rejects = session.query(ProxyDomainStatus.proxy_url).filter(and_(domain==ProxyDomainStatus.domain, 
	or_(ProxyDomainStatus.last_rejected >= last_rejected_threshold,  #rejected by the domain recently
		ProxyDomainStatus.last_accepted >= last_accepted_threshold
	)))
	proxy_lock_id = r.incr("proxy_lock_id")
	r.hset(domain, proxy_lock_id, session.query(Proxy).order_by(desc(Proxy.last_success)).filter(and_(or_( #pick the most recently non-defunct proxy
		Proxy.last_timeout < timeout_threshold,  #hasn't timed out in the last 2 days
			Proxy.last_success > Proxy.last_timeout), #or we had a success more recently than the timeout
		Proxy.consecutive_timeouts < max_consecutive_timeouts, #but we aren't going to keep trying if it keeps timing out over and over
		~Proxy.url.in_(rejects), ~Proxy.url.in_(r.hvals(domain)))).first().url) #not on the rejects list
	proxy = r.hget(domain, proxy_lock_id)
	r.hset(domain, proxy, proxy_lock_id)
	return session.query(Proxy).get(proxy)

def release_proxy(domain, proxy):
	proxy_lock_id = r.hget(domain, proxy)
	r.hdel(domain, proxy)
	r.hdel(domain, proxy_lock_id)
	return proxy_lock_id


def db(schema='arachnid', host='babel.priv.advisorconnect.co', user=DB_USER, pwd=DB_PASS):
    
    """
     Connect to the database
     
     :param schema: Schema name (defaults to arachnid)
     :param host:   Databse server name (defaults to babel)
     :param user:   Username (defaults to DB_USER constant)
     :param pwd:    Database password (defaults to DB_PASS constant)
     
     :returns :Engine A SQLAlchemy DB Engine instance

    """
    engine = None
    
    try:
        connection_url = "postgresql+psycopg2://{user}:{pwd}@{host}/{schema}".format(user=user, pwd=pwd, 
                                                                                         host=host, schema=schema)
    
        engine = sq.create_engine(connection_url, pool_size=1, isolation_level="READ_COMMITTED",
                                 strategy='threadlocal', echo=True, echo_pool=False)
    except Exception as e:
        print "Unable to connect to database, error: {}", str(e)
        raise
    finally:
        return engine

def robust_get_url(url, expected_xpaths, require_proxy=False, try_proxy=True):
	if not require_proxy:
		successful, response = try_request(url, expected_xpaths)
		if successful: return lxml.html.fromstring(response.content)
	if try_proxy:
		domain = get_domain(url)
		proxy = proc_pick_proxy(domain)
		while proxy:
			successful, response = try_request(url, expected_xpaths, proxy=proxy.url)
			if successful: 
				record_success(proxy, domain)
				#print proxy
				return lxml.html.fromstring(response.content)
			record_failure(proxy, domain, response)
			proxy = proc_pick_proxy(domain)
	else:
		r.sadd("urls",url)
		fn = url_to_s3_key(url)
		content = process_url(fn)
		while content is None and r.scard("urls")>0:
			content = process_url(fn)
		return lxml.html.fromstring(content)
	return None

#test
if __name__=="__main__":
	from prime.utils.googling import *
	from prime.prospects.get_prospect import *
	lauren = from_url("http://www.linkedin.com/in/laurentalbotnyc")
	search_query = extended_network_query_string(lauren)
	search_query = "http://www.google.com/search?q=site:www.linkedin.com+Daniel+Y.+Ng+California&es_sm=91&ei=NZxTVY_lB8mPyATvpoGACg&sa=N&num=100&start=0"
	raw_html = robust_get_url(search_query, google_xpaths, require_proxy=True)