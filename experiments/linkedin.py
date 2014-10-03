import re
import argparse
import json
import logging
import urlparse

from bs4 import BeautifulSoup

import phantomrunner
from models import ScrapeRequest, Session

logging.basicConfig(level=logging.DEBUG)

profile_re = re.compile('^https?://www.linkedin.com/pub/.*/.*/.*')

def is_profile_link(link):
    if link and re.match(profile_re, link):
	return True
    return False

def get_linked_profiles(html):
    soup = BeautifulSoup(html)

    profile_links = filter(is_profile_link, [ link.get('href') for link in soup.find_all('a') ])

    return [clean_url(pl) for pl in list(set(profile_links)) ]

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
    return s.decode('utf-8')

def process_next_request():
    session = Session()

    request = ScrapeRequest.get_unfinished_request(session)
    if request:
	logging.debug('Processing request {}'.format(request))

	content = clean_str(phantomrunner.get_content(request.url))
	linked_profiles = get_linked_profiles(content)
	request.done = True
	request.html = content

	for link in linked_profiles:
	    add_url(link, session, commit=False)
    else:
	logging.debug('There are currently no unfinished requests')

    session.commit()

def add_url(url, session=None, commit=True):
    if session is None:
	session = Session()

    if not session.query(ScrapeRequest).filter(ScrapeRequest.url==url).count():
	logging.debug('Adding scrape request for {} to the queue'.format(url))
	session.add(
	    ScrapeRequest(
		url = url
	    )
	)
    else:
	logging.debug('Skipping adding {} to the queue, already exists'.format(url))

    if session.commit:
	session.commit()

def process_forever():
    i = 0
    while True:
	process_next_request()
	logging.debug('Processed request #{}'.format(i))
	i+=1

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--add-url')
    parser.add_argument('--process-one', action='store_true')
    parser.add_argument('--process-forever', action='store_true')

    args = parser.parse_args()

    if args.process_one:
	process_next_request()
    elif args.add_url:
	add_url(args.add_url)
    elif args.process_forever:
	process_forever()
