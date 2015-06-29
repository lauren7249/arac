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

requests.packages.urllib3.disable_warnings()

timeout = 5
try_again_after_timeout_days = 2
max_consecutive_timeouts = 3
try_again_after_reject_days = 1
min_wait_btwn_requests_seconds = 15
max_wait_btwn_requests_seconds = 45

def try_request(url, expected_xpath, proxy=None):
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
	if response.status_code != 200: 
		#print response.status_code 
		return False, response
	raw_html = lxml.html.fromstring(response.content)
	#print response.content

	#"//script[contains(.,'background_view')]" for linkedin profile
	if len(raw_html.xpath(expected_xpath))==0: return False, response
	return True, response

def get_domain(url):
	url = re.sub(r"^https://","", url)
	url = re.sub(r"^http://","", url)	
	url = re.sub(r"^www.","", url)	
	return url.split("/")[0]

def record_failure(proxy, domain, response):
	now = datetime.utcnow()
	if response is None:
		proxy.last_timeout = now
		proxy.consecutive_timeouts+=1
		event = ProxyDomainEvent(proxy_url=proxy.url, domain=domain, event_time=now, success=False)
	else:
		proxy.last_success = now
		proxy.consecutive_timeouts=0
		status = session.query(ProxyDomainStatus).get((proxy.url,domain))
		if status is None: status = ProxyDomainStatus(proxy_url=proxy.url, domain=domain, last_rejected=datetime.fromtimestamp(0), last_accepted=datetime.fromtimestamp(0))
		status.last_rejected = now
		event = ProxyDomainEvent(proxy_url=proxy.url, domain=domain, event_time=now, status_code=response.status_code, success=False)
		session.add(status)	
	session.add(proxy)	
	session.add(event)
	session.flush()
	session.commit()

def record_success(proxy, domain):
	now = datetime.utcnow()
	proxy.last_success = now
	proxy.consecutive_timeouts=0
	session.add(proxy)
	status = session.query(ProxyDomainStatus).get((proxy.url,domain))
	if status is None: status = ProxyDomainStatus(proxy_url=proxy.url, domain=domain, last_rejected=datetime.fromtimestamp(0), last_accepted=datetime.fromtimestamp(0))
	status.last_accepted = now
	event = ProxyDomainEvent(proxy_url=proxy.url, domain=domain, event_time=now, status_code="200", success=True)
	session.add(status)	
	session.add(event)
	session.flush()
	session.commit()

#return Proxy object
def pick_proxy(domain):
	#keep wait time random
	wait_btwn_requests_seconds = randint(min_wait_btwn_requests_seconds, max_wait_btwn_requests_seconds)
	rejects = session.query(ProxyDomainStatus.proxy_url).filter(and_(domain==ProxyDomainStatus.domain, 
	or_(ProxyDomainStatus.last_rejected >= (datetime.utcnow() - timedelta(days=try_again_after_reject_days)),  #rejected by the domain recently
		ProxyDomainStatus.last_rejected >= (datetime.utcnow() - timedelta(seconds=wait_btwn_requests_seconds)), #tried very recently
		ProxyDomainStatus.last_accepted >= (datetime.utcnow() - timedelta(seconds=wait_btwn_requests_seconds))
	)))
	proxy_lock_id = r.incr("proxy_lock_id")
	r.hset(domain, proxy_lock_id, session.query(Proxy).order_by(desc(Proxy.last_success)).filter(and_(or_( #pick the most recently non-defunct proxy
		Proxy.last_timeout < (datetime.utcnow() - timedelta(days=try_again_after_timeout_days)),  #hasn't timed out in the last 2 days
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

def robust_get_url(url, expected_xpath, require_proxy=True):
	if not require_proxy:
		successful, response = try_request(url, expected_xpath)
		if successful: return lxml.html.fromstring(response.content)
	domain = get_domain(url)
	proxy = pick_proxy(domain)
	while proxy:
		successful, response = try_request(url, expected_xpath, proxy=proxy.url)
		release_proxy(domain, proxy.url)
		if successful: 
			record_success(proxy, domain)
			#print proxy
			return lxml.html.fromstring(response.content)
		record_failure(proxy, domain, response)
		proxy = pick_proxy(domain)
	return None