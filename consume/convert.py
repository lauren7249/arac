import json
import lxml.html
from lxml import etree
import os
import re
import argparse
import urlparse
import logging

#from bs4 import BeautifulSoup, SoupStrainer

profile_re = re.compile('^https?://www.linkedin.com/pub/.*/.*/.*')
member_re  = re.compile("member-")


def convert(filename, writefile):
    file = open(filename, 'r').read()
    html = json.loads(file).get("content")
    soup = BeautifulSoup(html)
    result = parse_html(html)
    writefile.write(unicode(json.dumps(result)).decode("utf-8", "ignore"))
    return True

def main():
    os.chdir("data")
    for filename in os.listdir(os.getcwd()):
        file = open(filename, 'r').read()
        html = json.loads(file).get("content")
        results =  parse_html(html)
        #print "File:{0}, Jobs: {1}, Schools:{2}".format(filename,\
        #        len(results.get("experiences", 0)),
        #        len(results.get("schools", 0)))

def debug():
    #file = open("data/http:www.linkedin.compubzachary-kowalski37372872", 'r').read()
    file = open("data/http:www.linkedin.compubalbie-solis1ab8b34", 'r').read()
    html = json.loads(file).get("content")
    return parse_html(html)

def is_profile_link(link):

    if link and re.match(profile_re, link):
        return True
    return False

def get_linked_profiles(html):
    return list(set(re.findall('https?://www.linkedin.com/pub/.*/.*/.*', html)))

def safe_clean_str(s):
    if s:
        return s.strip()
    return s

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

def find_profile_jobs(raw_html):
    jobs = []
    profile_jobs = raw_html.xpath("//div[@id='profile-experience']")[0]
    for item in profile_jobs.xpath(".//div[contains(@class, 'position ')]"):
        dict_item = {}
        title = item.find(".//h3")
        if title is not None:
            dict_item["title"] = safe_clean_str(title.text_content())
        company = item.find(".//h4")
        if company is not None:
            dict_item["company"] = safe_clean_str(company.text_content())
        dates = item.findall(".//abbr")
        if len(dates) > 1:
            dict_item["start_date"] = dates[0].get('title')
            dict_item["end_date"] = dates[1].get('title')
        if len(dates) == 1:
            import pdb
            pdb.set_trace()
            dict_item["start_date"] = dates[0].get('text')
            dict_item["end_date"] = "Present"
        location = item.xpath(".//span[@class='location']")
        if len(location) > 0:
            dict_item['location'] = safe_clean_str(location[0].text_content())
        description = item.xpath(".//p[contains(@class, ' description ')]")
        if len(description) > 0:
            dict_item["description"] = safe_clean_str(description[0].text_content())
        jobs.append(dict_item)
    return jobs

def find_background_jobs(raw_html):
    jobs = []
    background_jobs = raw_html.xpath("//div[@id='background-experience']/div")
    for item in background_jobs:
        dict_item = {}
        title = item.find(".//h4")
        if title is not None:
            dict_item["title"] = safe_clean_str(title.text_content())
        company = item.findall(".//h5")
        if len(company) == 2:
            dict_item["company"] = safe_clean_str(company[1].text_content())
        else:
            dict_item["company"] = safe_clean_str(company[0].text_content())
        location = item.xpath(".//span[@class='locality']")
        if len(location) > 0:
            dict_item['location'] = safe_clean_str(location[0].text_content())
        description = item.xpath(".//p[contains(@class, 'description')]")
        if len(description) > 0:
            dict_item["description"] = safe_clean_str(description[0].text_content())
        dates = item.findall(".//time")
        if len(dates) > 1:
            dict_item["start_date"] = safe_clean_str(dates[0].text_content())
            dict_item["end_date"] = safe_clean_str(dates[1].text_content())
        if len(dates) == 1:
            dict_item["start_date"] = safe_clean_str(dates[0].text_content())
            dict_item["end_date"] = "Present"
        jobs.append(dict_item)
    return jobs


def find_profile_schools(raw_html):
    schools = []
    profile_jobs = raw_html.xpath("//div[@id='profile-education']")[0]
    for item in profile_jobs.xpath(".//div[contains(@class, 'position ')]"):
        dict_item = {}
        college = item.find(".//h3")
        if college is not None:
            dict_item["college"] = safe_clean_str(college.text_content())
        degree = item.find(".//h4")
        if degree is not None:
            dict_item["degree"] = safe_clean_str(degree.text_content())
        dates = item.findall(".//abbr")
        if len(dates) > 1:
            dict_item["start_date"] = dates[0].get('title')
            dict_item["end_date"] = dates[1].get('title')

        present = "Present" in etree.tostring(item, pretty_print=True)
        if len(dates) == 1 and not present:
            dict_item["graduation_date"] = dates[0].get('title')
        if len(dates) == 1 and present:
            dict_item["start_date"] = dates[0].get('title')
            dict_item["end_date"] = "Present"

        description = item.xpath(".//p[contains(@class, 'desc ')]")
        if len(description) > 0:
            dict_item["description"] = safe_clean_str(description[0].text_content())
        schools.append(dict_item)
    return schools

def find_background_schools(raw_html):
    schools = []
    background_schools = raw_html.xpath("//div[@id='background-education']/div")
    for item in background_schools:
        dict_item = {}
        college = item.find(".//h4")
        if college is not None:
            dict_item["college"] = safe_clean_str(college.text_content())
        degrees = item.findall(".//h5")
        if len(degrees) == 2:
            dict_item["degree"] = safe_clean_str(degrees[1].text_content())
        if len(degrees) == 1:
            dict_item["degree"] = safe_clean_str(degrees[0].text_content())
        dates = item.findall("time")
        if len(dates) > 1:
            dict_item["start_date"] = safe_clean_str(dates[0].text_content())
            dict_item["end_date"] = safe_clean_str(dates[1].text_content().encode('ascii', 'ignore'))

        present = "Present" in etree.tostring(item, pretty_print=True)
        if len(dates) == 1 and not present:
            dict_item["graduation_date"] = dates[0].text_content()
        if len(dates) == 1 and present:
            dict_item["start_date"] = dates[0].text_content()
            dict_item["end_date"] = "Present"

        description = item.xpath(".//p[contains(@class, ' desc ')]")
        if len(description) > 0:
            dict_item["description"] = safe_clean_str(description[0].text_content())
        schools.append(dict_item)
    return schools


def parse_html(html):
    raw_html = lxml.html.fromstring(html)

    full_name = None
    try:
        full_name = raw_html.xpath("//span[@class='full-name']")[0].text_content()
    except:
        pass

    try:
        linkedin_index = html.find("newTrkInfo='") + 12
        end_index = html[linkedin_index:].find("'")
        linkedin_id = html[linkedin_index:linkedin_index+end_index].replace(",", "")
    except:
        linkedin_id = None

    location = None
    industry = None
    try:
        all_dd = raw_html.xpath("//div[@id='location']/dd")
        location = all_dd[0].text
        industry = all_dd[1].text
    except:
        try:
            location = raw_html.xpath("//span[@class='locality']")[0].text
            industry = raw_html.xpath("//dd[@class='industry']")[0].text
        except:
            pass


    location = safe_clean_str(location)
    industry = safe_clean_str(industry)

    connections = None
    try:
        connections = raw_html.xpath("//div[@class='member-connections']").text_content()
        connections = "".join(re.findall("\d+", connections))
    except:
        try:
            connections = raw_html.xpath("//dd[@class='overview-connections']")[0].text_content()
            connections = "".join(re.findall("\d+", connections))
        except:
            pass

    experiences = []
    schools = []
    if len(raw_html.xpath("//div[@id='profile-experience']")) > 0:
        experiences = find_profile_jobs(raw_html)

    if len(raw_html.xpath("//div[@id='background-experience']")) > 0:
        experiences = find_background_jobs(raw_html)

    school_type = None
    if len(raw_html.xpath("//div[@id='profile-education']")) > 0:
        schools = find_profile_schools(raw_html)

    if len(raw_html.xpath("//div[@id='background-education']")) > 0:
        experiences = find_background_schools(raw_html)


    skills = [e.text_content() for e in raw_html.xpath("//li[@class='endorse-item']")]
    people = get_linked_profiles(html)

    print experiences
    return {
        'linkedin_id': linkedin_id,
        'full_name': full_name,
        'schools': schools,
        'experiences': experiences,
        'skills': skills,
        'people': people,
        'connections': connections,
        'location': location,
        'industry': industry
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--benchmark', action='store_true')
    args = parser.parse_args()

    if args.benchmark:
        import timeit
        print(timeit.timeit("debug()", setup="from __main__ import debug",
            number=10000))
    else:
        main()


