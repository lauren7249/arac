import requests
import argparse
import lxml.html
import re

requests.packages.urllib3.disable_warnings()

headers ={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}

def find_linkedin_url(url):
    query = "https://www.linkedin.com/company/" 
    URL = "http://www.google.com/search?num=100&q={}&oq={}&aqs=chrome..69i57.6893j0j1&sourceid=chrome&es_sm=91&ie=UTF-8"
    results = set()
    URL = URL.format(query, query)
    while URL is not None:
        proxies = {"http": "http://54.246.92.203", "https":"http://69.12.64.106"}        
        result = requests.get(URL, headers=headers)
        crawlable = lxml.html.fromstring(result.content)
        links = [ad.text_content() \
                for ad in crawlable.xpath("//cite[@class='_Rm']")]
        for link in links:
            if re.match(r"^https://www.linkedin.com/company/[A-Za-z0-9]+", link):
                results.add(link)
                print link
        try:
            next_results_page = crawlable.xpath("//a[@class='pn']")[0].xpath("./@href")[0]
            next_results_page = next_results_page[next_results_page.find(query) + len(query):]
            next_results_page = re.sub("%22","", next_results_page)
            next_results_page = 'http://www.google.com/search?q="' + query + '"' + next_results_page
            print next_results_page
        except:
            break
        URL = next_results_page
        if len(results) > 2: break
        break
    print results
    print str(len(results))
    #print result.content

if __name__ == "__main__":
    # parser = argparse.ArgumentParser()
    # parser.add_argument('url')
    # args = parser.parse_args()
    find_linkedin_url("")
