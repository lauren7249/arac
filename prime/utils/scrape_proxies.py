import lxml.html
import requests
import os, re
from geoip import geolite2
import redis

ua='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'
headers ={'User-Agent':ua}
timeout=8
ip_regex = re.compile(r"(^|[^0-9\.])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?=$|[^0-9\.])")
port_regex = re.compile(r"(^|[^0-9\.])\d{1,5}(?=$|[^0-9\.])")
secret_sauce = "&es_sm=91&ei=NZxTVY_lB8mPyATvpoGACg&sa=N"
host='proxies.sqq1to.0001.euc1.cache.amazonaws.com'

def get_redis(flush=False):
	pool = redis.ConnectionPool(host=host, port=6379, db=0)
	r = redis.Redis(connection_pool=pool)
	if flush: r.flushall()
	return r

r = get_redis() 

def get_proxies(site='xroxy', redis=r, overwrite=False):
	if site == "hidemyass":
		get_hidemyass_proxies(redis=redis, overwrite=overwrite)
	elif site == "proxylistorg":
		get_proxylistorg_proxies(redis=redis, overwrite=overwrite)
	elif site == "xroxy":
		get_xroxy_proxies(redis=redis, overwrite=overwrite)
	elif site == "google":
		get_google_proxies(redis=redis, overwrite=overwrite)

def parse_line(line):
	match = re.search(ip_regex,line)
	if match is None: return None
	#something looks like an ip, lets clean it
	ip = re.sub(r"[^0-9\.]","",match.group(0))
	ip_nums = [int(piece) for piece in ip.split(".")]
	if max(ip_nums)>255: return None
	ip=".".join([str(piece) for piece in ip_nums])
	#the ip is in valid format
	match = re.search(port_regex,line[match.end():])
	if match is None: return None
	port = int(re.sub(r"[^0-9]","",match.group(0)))
	if port>65535: return None
	port = str(port)
	return ip + ":" + port

def queue_proxy(redis=r, source=None, proxy=None):
	if proxy is not None and redis is not None: 
		r.lpush("untested_proxies", {"source":source,"proxy":proxy})

def get_ip(raw):
	chunks = raw.split(":")
	if len(chunks) == 2: return chunks[0]
	return chunks[1][2:]

def get_google_proxies(redis=r, overwrite=False, proxies_query="%2B%22:8080%22+%2B%22:3128%22+%2B%22:80%22+filetype:txt", results_per_page=100, start_num=0):
	urls = []
	while True:
		search_query ="http://www.google.com/search?q=" + proxies_query + secret_sauce + "&num=" + str(results_per_page) + "&start=" + str(start_num) 
		start_num+=results_per_page
		response = requests.get(search_query, headers=headers, verify=False)
		raw_html = lxml.html.fromstring(response.content)
		results_area = raw_html.xpath("//*[contains(@class,'srg')]")
		if len(results_area) == 0: break
		links = results_area[0].xpath("//h3[@class='r']/a")
		for link in links:
			urls.append(link.values()[0])

	for url in urls:
		try: response = requests.get(url, headers=headers, verify=False, timeout=timeout)
		except: continue
		for line in response.content.splitlines():
			proxy = parse_line(line)
			if proxy is None: continue
			ip = get_ip(proxy)
			match = geolite2.lookup(ip)
			if match is None or match.country is None or match.continent is None: continue
			queue_proxy(redis=r,source=url,proxy=proxy)

#return a dict of fresh hidemyass proxies
def get_hidemyass_proxies(limit=None, redis=r, overwrite=False):
	from headless_browsing import launch_browser
	proxies = []
	display, driver = launch_browser()
	driver.implicitly_wait(2)
	source = "http://proxylist.hidemyass.com/"
	page = 1
	while True:
		try:
			driver.get(source + str(page))
			body = driver.find_element_by_tag_name("tbody")
			trs = body.find_elements_by_tag_name("tr")
			if len(trs) == 0: break
			for tr in trs:
				ip = ""
				tds = tr.find_elements_by_tag_name("td")
				td = tds[1]
				divs = td.find_elements_by_tag_name("div")
				spans = td.find_elements_by_tag_name("span")
				texts = divs + spans
				for element in texts:
				    if not element.is_displayed(): continue
				    ip = ip + element.text
				    if re.match(ip_regex,element.text): break
				port = tds[2].text.strip()
				protocol =  tds[6].text.strip()
				if protocol.find("HTTP") == -1: continue
				proxy = protocol.lower() + "://" + ip + ":" + port
				proxies.append(proxy)
				queue_proxy(redis=r,proxy=proxy,source=source)
				if limit is not None and len(proxies) == limit: 
					driver.quit()
					return proxies
		except:
			driver.save_screenshot('screenshot.png')
			break
		page += 1

	driver.quit()
	return proxies

def get_proxylistorg_proxies(redis=r, overwrite=False):
	proxies = []
	page = 0
	source = 'http://proxy-list.org/english/index.php'
	while True:	
		response = requests.get(source + '?p=' + str(page), timeout=timeout, headers=headers)
		raw_html = lxml.html.fromstring(response.content)
		table = raw_html.xpath("//div[@class='table']")[0]
		proxies_d = table.xpath("//ul/li[@class='proxy']")
		protocols_d = table.xpath("//ul/li[@class='https']")
		if len(proxies_d) < 2: break
		for i in xrange(1,len(proxies_d)):
			proxy = proxies_d[i].text_content()
			protocol = protocols_d[i].text_content()
			if protocol in ["HTTP","HTTPS"]:
				proxy = protocol.lower() + "://" + proxy
				proxies.append(proxy)
				queue_proxy(redis=r,proxy=proxy,source=source)
			# else:
			# 	proxies.append("http://"+proxy)
			# 	proxies.append("https://"+proxy)		
		page += 1
				
	return proxies

def get_xroxy_proxies(redis=r, overwrite=False):
	proxies = []
	page = 0
	source = 'http://www.xroxy.com/proxylist.php'
	while True:	
		try:
			response = requests.get(source + '?&pnum=' + str(page), verify=False, timeout=timeout, headers=headers)
		except:
			return None
		#print response.status_code
		raw_html = lxml.html.fromstring(response.content)
		table = raw_html.xpath("//table")[0]
		proxies_d = table.xpath("//tr/td/a[@title='View this Proxy details']")
		ports_d = table.xpath("//tr/td/a[contains(@title,'Select proxies with port number')]")  
		protocols_d = table.xpath("//tr/td/a[@title='Select proxies with/without SSL support']")
		#print len(proxies_d)
		if len(proxies_d) < 2: break
		for i in xrange(0,len(proxies_d)):
			proxy = proxies_d[i].text_content().strip()
			port = ports_d[i].text_content().strip()
			protocol = protocols_d[i].text_content().strip()
			if protocol == 'true':
				proxy = "https://"+proxy+":"+port
			elif protocol == 'false':
				proxy = "http://"+proxy+":"+port
			else: continue
			proxies.append(proxy)
			queue_proxy(redis=r,proxy=proxy,source=source)
			# else:
			# 	proxies.append("http://"+proxy+":"+port)
			# 	proxies.append("https://"+proxy+":"+port)		
		#print len(proxies)
		page += 1	
	return proxies	
