import requests
import argparse
import lxml.html
import re

URL = "https://www.google.com/search?q={}&oq={}&aqs=chrome..69i57.6893j0j1&sourceid=chrome&es_sm=91&ie=UTF-8"
headers ={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def find_linkedin_url(url):
    query = "https://www.linkedin.com/company/" 
    LINKEDIN_URL = "https://www.google.com/search?q={}&oq={}&aqs=chrome..69i57.6893j0j1&sourceid=chrome&es_sm=91&ie=UTF-8"
    result = requests.get(LINKEDIN_URL.format(query, query), headers=headers)
    print result.text
    crawlable = lxml.html.fromstring(result.content)
    links = [ad.text_content() \
            for ad in crawlable.xpath("//cite[@class='_Rm']")]
    for link in links:
        if re.match(r"^https://www.linkedin.com/company/[A-Za-z0-9]+", link):
            print link

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument('url')
    # args = parser.parse_args()
    find_linkedin_url("")
