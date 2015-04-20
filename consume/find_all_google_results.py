import requests
import argparse
import lxml.html

URL = "https://www.google.com/search?q={}&oq={}&aqs=chrome..69i57.6893j0j1&sourceid=chrome&es_sm=91&ie=UTF-8"
headers ={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def find_linkedin_url(url):
    query = "https://www.linkedin.com/company/" 
    LINKEDIN_URL = "https://www.google.com/search?q={}&oq={}&aqs=chrome..69i57.6893j0j1&sourceid=chrome&es_sm=91&ie=UTF-8"
    result = requests.get(LINKEDIN_URL.format(query, query), headers=headers)
    crawlable = lxml.html.fromstring(result.content)
    links = [ad.xpath("./@href")[0] \
            for ad in crawlable.xpath("//h3/a")]
    for link in links:
        if 'company' in link:
            print link
            return link

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument('url')
    # args = parser.parse_args()
    find_linkedin_url("")
