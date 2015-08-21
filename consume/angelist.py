from prime.utils import *
import lxml.html
import sys
def get_angellist_info(angellist_url):
	info = {}
	response = requests.get(angellist_url, headers=headers)
	raw_html = lxml.html.fromstring(response.content)
	try:
		category = raw_html.xpath(".//div[@class='tags']")[0].text_content().strip().split("\n")[0]
		info['category'] = category
	except: pass
	try:
		followers = raw_html.xpath(".//a[contains(@class,'followers_count')]")[0].text_content().strip().split(" ")[0]
		info['followers'] = int(followers)
	except: pass
	try:
		following = raw_html.xpath(".//a[contains(@class,'following_count')]")[0].text_content().strip().split(" ")[0]
		info["following"] = int(following)
	except:pass
	try:
		investments_url = "https://angel.co" + raw_html.xpath(".//div[contains(@data-load_url,'/startup_roles/investments')]")[0].get("data-load_url")
		response = requests.get(investments_url, headers=headers)
		investments = json.loads(response.content)
		info['investments'] = investments
	except Exception, e: 
		print(sys.exc_info()[0])
	return info

