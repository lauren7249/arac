import re
import os
import logging
import urlparse
import argparse

from bs4 import BeautifulSoup

from boto import kinesis

import phantom_runner

profile_re = re.compile('^https?://www.linkedin.com/pub/.*/.*/.*')

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

    return profile_links

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
    content = phantom_runner.get_content(url)
    linked_profiles = get_linked_profiles(content)

    result = {
        'url': url,
        'links': linked_profiles,
        'content': content
    }
    print linked_profiles
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()

    process_request(args.url)
