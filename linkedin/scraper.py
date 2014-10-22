import re
import os
import logging
import urlparse

from bs4 import BeautifulSoup

from boto import kinesis

import phantomrunner

profile_re = re.compile('^https?://www.linkedin.com/pub/.*/.*/.*')

def is_profile_link(link):
    if link and re.match(profile_re, link):
        return True
    return False

def get_linked_profiles(html):
    soup = BeautifulSoup(html)
    profile_links = filter(is_profile_link, [ link.get('href') for link in soup.find_all('a') ])

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
    content = phantomrunner.get_content(url)
    linked_profiles = get_linked_profiles(content)

    result = {
        'url': url,
        'links': linked_profiles,
        'content': content
    }

    session.commit()


redis_conn = Redis(os.getenv(
queue = Queue(connection=redis_conn)




