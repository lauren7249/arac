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

def process_request(url):
    ua = UserAgent()
    response = requests.get(url, headers={'User-agent': ua.random}, timeout=10)
    content = response.content
    print content

    if len(content) < MINIMUM_CONTENT_SIZE: 
        raise ScraperLimitedException(
            'Server response is less than {} in size'.format(
                MINIMUM_CONTENT_SIZE
            )
        )

    if response.status_code == 999:
        raise ScraperLimitedException('Server responded with 999')

    linked_profiles = get_linked_profiles(content)

    result = {
        'url': url,
        'links': linked_profiles,
        'status': response.status_code,
        'content': content
    }

    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()

    process_request(args.url)
