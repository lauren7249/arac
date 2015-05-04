import re
import requests
import os
import logging
import urlparse
import argparse

from bs4 import BeautifulSoup

from fake_useragent import UserAgent

profile_re = re.compile('^https?://www.linkedin.com/pub/.*/.*/.*')

MINIMUM_CONTENT_SIZE = 1000

class ScraperLimitedException(Exception):
    pass

def is_profile_link(link):

    if link and re.match(profile_re, link):
        return True
    return False

def get_linked_profiles(html):
    soup = BeautifulSoup(html)
    profile_links = filter(is_profile_link, [
        clean_url(link.get('href')) for link in
        soup.find_all('a') if link.get('href')
    ])

    return list(set(profile_links))

def clean_url(s):
    pr = urlparse.urlparse(s)

    return urlparse.urlunparse((
        pr.scheme,
        pr.netloc,
        pr.path,
        '',
        '',
        ''
    ))

def clean_str(s):
    return s.decode('utf-8', 'ignore')

def make_request(url):
    new_url = "http://api.phantomjscloud.com/single/browser/v1/48ac5de24ddc92bd0c900ba0d45cc397dd6002f9/?requestType=raw&targetUrl={}&loadImages=false&abortOnJavascriptErrors=false&isDebg=false&postDomLoadedTimeout=10000&userAgent=Mozilla/5.0+(Windows+NT+6.1)+AppleWebKit/537.36+(KHTML,+like+Gecko)+Chrome/28.0.1468.0+Safari/537.36+PhantomJsCloud/1.1&geolocation=us"
    response = requests.get(new_url.format(url), verify=False)
    content = response.content
    return content

def process_request(url):
    content = make_request(url)
    max_retries = 10
    retries = 0

    while retries < 10:
        if len(content) < MINIMUM_CONTENT_SIZE:
            retries += 1
            content = make_request(url)
        else:
            break
            
    if len(content) < MINIMUM_CONTENT_SIZE:
        raise ScraperLimitedException(
            'Server response is less than {} in size'.format(
                MINIMUM_CONTENT_SIZE
            )
        )

    linked_profiles = get_linked_profiles(content)

    result = {
        'url': url,
        'links': linked_profiles,
        'content': content
    }

    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()

    process_request(args.url)
