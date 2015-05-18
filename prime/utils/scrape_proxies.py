
from selenium import webdriver
import re
from pyvirtualdisplay import Display
from headless_browsing import * 

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
				d = {"ip": ip, "port": port, "protocol": protocol}
				proxies.append(d)
				if redis is not None:
					proxy = protocol.lower() + "://" + ip + ":" + port
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

