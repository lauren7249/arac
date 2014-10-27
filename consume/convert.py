import csv
import urlparse
import os
import json
import sys
import re
import argparse
from itertools import islice
from contextlib import contextmanager

from py2neo import neo4j, node, rel

from bs4 import BeautifulSoup

profile_re = re.compile('^https?://www.linkedin.com/pub/.*/.*/.*')

def main():
    os.chdir("data")
    for filename in os.listdir(os.getcwd()):
        i = 0
        file = open(filename, 'r').read()
        html = json.loads(file).get("content")
        soup = BeautifulSoup(html)
        result = parse_html(html)

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

def first_or_none(l):
    result = l[0] if l else None
    if result:
        return result

def remove_dups(l):
    return list(set(l))

def getnattr(item, attribute, default=None):
    if item:
        return getattr(item, attribute, default)
    return None

def soup_loop(soup, parent_id, child, child_kwargs, **kwargs):
    items = []
    for item in soup.find(id=parent_id).find_all(child, **child_kwargs):
        dict_item = {}
        for k, v in kwargs.iteritems():
            value = item.find(v)
            dict_item[k] = getnattr(value, 'text')
        items.append(dict_item)
    return items

def find_jobs(soup):
    jobs = []
    try:
        jobs = soup_loop(soup,
                "profile-experience",
                "div",
                {"class": "position"},
                **{
                    "title": "h3",
                    "company": "h4",
                    "start_date": "abbr#dtstart",
                    "description": "p.description",
                    "end_date": "dtstamp"
                    }
                )
        return jobs
    except Exception, e:
        print "Error: {}".format(e)
        pass

    try:
        jobs = soup_loop(soup,
                "background-experience",
                "div",
                {},
                **{
                    "title": "h4",
                    "company": "h5",
                    "start_date": "time",
                    "description": "description",
                    "end_date": "time"
                    }
                )
        return jobs
    except Exception, e:
        print "Error: {}".format(e)
        pass
    return None

def find_schools(soup):
    schools = []
    try:
        schools = soup_loop(soup,
                "profile-education",
                "div",
                {"class": "position"},
                **{
                    "college": "h3",
                    "degree": "h4",
                    "graduation": "p.period",
                    "start_date": "abbr#dtstart",
                    "description": "p.description",
                    "end_date": "dtstamp"
                    }
                )
        return schools
    except Exception, e:
        print "Error: {}".format(e)
        pass

    try:
        schools = soup_loop(soup,
                "background-education",
                "div",
                {},
                **{
                    "college": "h4",
                    "degree": "h5",
                    "start_date": "time",
                    "end_date": "time"
                    }
                )
        return schools
    except Exception, e:
        print "Error: {}".format(e)
        pass
    return None

def parse_html(html):
    soup = BeautifulSoup(html)

    full_name = None
    full_name_el = first_or_none(soup.find_all(class_='full-name'))
    if full_name_el:
        full_name = full_name_el.text.strip()


    try:
        location = soup.find("div", id='location').find_all("dd")[0].text
        industry = soup.find("div", id='location').find_all("dd")[1].text
    except:
        try:
            location = soup.find("span", {'class': 'locality'}).text
            industry = soup.find("dd", {'class': "industry"}).text
        except:
            location = None
            industry = None
    try:
        connections = soup.find("div", {"class": "member-connections"}).text.split("connections")[0]
    except:
        try:
            connections = soup.find("dd", {'class': "overview-connections"}).text
        except:
            connections = None
    experiences = find_jobs(soup)
    #schools = find_schools(soup)
    #skills = [e.text for e in soup.find_all("li", {'class': 'endorse-item'})]
    people = get_linked_profiles(html)

    return {
        'full_name': full_name,
        #'schools': schools,
        'experiences': experiences,
        #'skills': skills,
        'people': people,
        'connections': connections,
        'location': location,
        'industry': industry
    }


if __name__ == '__main__':
    main()
