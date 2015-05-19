
from selenium import webdriver
import re
from pyvirtualdisplay import Display
from headless_browsing import * 
import lxml.html
import requests

ip_regex = re.compile(r"(^|[^0-9\.])\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(?=$|[^0-9\.])")

#return a dict of fresh hidemyass proxies
def get_hidemyass_proxies(limit=None, redis=None, overwrite=False):
	proxies = []
	display, driver = launch_browser()
	driver.implicitly_wait(2)

	page = 1
	while True:
		try:
			driver.get("http://proxylist.hidemyass.com/" + str(page))
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
				if redis is not None:
					if not redis.sismember("blacklist_proxies",proxy) or overwrite: 
						redis.sadd("proxies",proxy)
						print redis.scard("proxies")
					else:
						print "proxy exists"
				if limit is not None and len(proxies) == limit: 
					driver.quit()
					return proxies
		except:
			driver.save_screenshot('screenshot.png')
			break
		page += 1

	driver.quit()
	return proxies

def get_proxylistorg_proxies(redis=None, overwrite=False):
	proxies = []
	page = 0
	while True:	
		response = requests.get('http://proxy-list.org/english/index.php?p=' + str(page))
		raw_html = lxml.html.fromstring(response.content)
		table = raw_html.xpath("//div[@class='table']")[0]
		proxies_d = table.xpath("//ul/li[@class='proxy']")
		protocols_d = table.xpath("//ul/li[@class='https']")
		if len(proxies_d) < 2: break
		for i in xrange(1,len(proxies_d)):
			proxy = proxies_d[i].text_content()
			protocol = protocols_d[i].text_content()
			if protocol in ["HTTP","HTTPS"]:
				proxies.append(protocol.lower() + "://" + proxy)
			else:
				proxies.append("http://"+proxy)
				proxies.append("https://"+proxy)		
		page += 1
	if redis is not None:
		for proxy in proxies:
			if not redis.sismember("blacklist_proxies",proxy) or overwrite: 
				redis.sadd("proxies",proxy)
				print redis.scard("proxies")
			else:
				print "proxy exists"		
	return proxies

def get_xroxy_proxies(redis=None, overwrite=False):
	proxies = []
	page = 0
	while True:	
		response = requests.get('http://www.xroxy.com/proxylist.php?port=&type=&ssl=&country=&latency=&reliability=&sort=reliability&desc=true&pnum=' + str(page))
		raw_html = lxml.html.fromstring(response.content)
		table = raw_html.xpath("//table")[0]
		proxies_d = table.xpath("//tr/td/a[@title='View this Proxy details']")
		ports_d = table.xpath("//tr/td/a[contains(@title,'Select proxies with port number')]")  
		protocols_d = table.xpath("//tr/td/a[@title='Select proxies with/without SSL support']")
		if len(proxies_d) < 1: break
		for i in xrange(0,len(proxies_d)):
			proxy = proxies_d[i].text_content().strip()
			port = ports_d[i].text_content().strip()
			protocol = protocols_d[i].text_content().strip()
			if protocol == 'true':
				proxies.append("https://"+proxy+":"+port)
			elif protocol == 'false':
				proxies.append("http://"+proxy+":"+port)
			else:
				proxies.append("http://"+proxy+":"+port)
				proxies.append("https://"+proxy+":"+port)		
		page += 1
	if redis is not None:
		for proxy in proxies:
			if not redis.sismember("blacklist_proxies",proxy) or overwrite: 
				redis.sadd("proxies",proxy)
				print redis.scard("proxies")
			else:
				print "proxy exists"		
	return proxies	
