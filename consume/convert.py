import json
import os
import re
import argparse
import urlparse
import logging

from bs4 import BeautifulSoup

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
    writefile = open("resuts.json", "a+")
    os.chdir("data")
    i = 0
    logging.info("Creating a pool")
    pool = GreenPool(size=20)
    for filename in os.listdir(os.getcwd()):
        pool.spawn_n(convert, filename, writefile)
        i += 1
        sys.stdout.write("\r%.2f%% %s" % (float(i)/10000, i))
        sys.stdout.flush()
    pool.waitall()

def debug():
    os.chdir("data")
    for filename in os.listdir(os.getcwd()):
        file = open(filename, 'r').read()
        html = json.loads(file).get("content")
        soup = BeautifulSoup(html)
        cleaned = parse_html(html)
        for school in cleaned.get("schools"):
            print school.get("end_date"), school.get("start_date"),\
                    school.get("graduation_date")

        for job in cleaned.get("experiences"):
            print job.get("end_date"), job.get("start_date")

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

def find_profile_jobs(profile_jobs, soup):
    jobs = []
    for item in profile_jobs.find_all("div", {"class": "position"}):
        dict_item = {}
        dict_item["title"] = safe_clean_str(getnattr(item.find("h3"), 'text'))
        dict_item["company"] = safe_clean_str(getnattr(item.find("h4"), 'text'))
        dates = item.find_all("abbr")
        if len(dates) > 1:
            dict_item["start_date"] = dates[0].get('title')
            dict_item["end_date"] = dates[1].get('title')
        if len(dates) == 1:
            dict_item["start_date"] = dates[0].get('text')
            dict_item["end_date"] = "Present"
        dict_item['location'] = safe_clean_str(getnattr(item.find("span",\
            {"class": "location"}), 'text'))
        dict_item["description"] = safe_clean_str(getnattr(item.find("p",\
                class_='description'), 'text'))

        jobs.append(dict_item)
    return jobs

def find_background_jobs(background_jobs):
    jobs = []
    for item in background_jobs.find_all("div"):
        dict_item = {}
        dict_item["title"] = safe_clean_str(getnattr(item.find("h4"), 'text'))
        company = item.find_all("h5")
        if len(company) == 2:
            dict_item["company"] = safe_clean_str(getnattr(company[1], 'text'))
        else:
            dict_item["company"] = safe_clean_str(getnattr(company[0], 'text'))
        dict_item['location'] = safe_clean_str(getnattr(item.find("span",\
            {"class": "locality"}), 'text'))
        dict_item["description"] = safe_clean_str(getnattr(item.find("p",\
                class_='description'), 'text'))
        dates = item.find_all("time")
        if len(dates) > 1:
            dict_item["start_date"] = getnattr(dates[0], 'text')
            dict_item["end_date"] = getnattr(dates[1], 'text')
        if len(dates) == 1:
            dict_item["start_date"] = getnattr(dates[0], 'text')
            dict_item["end_date"] = "Present"

        jobs.append(dict_item)
    return jobs

def find_jobs(soup):
    jobs = []
    profile_jobs = soup.find(id="profile-experience")
    background_jobs = soup.find(id="background-experience")
    if profile_jobs:
        jobs = find_profile_jobs(profile_jobs, soup)
    if background_jobs:
        jobs = find_background_jobs(background_jobs)

    return jobs

def find_profile_schools(profile_schools):
    schools = []
    for item in profile_schools.find_all("div", {"class": "position"}):
        dict_item = {}
        dict_item["college"] = safe_clean_str(getnattr(item.find("h3"), 'text'))
        dict_item["degree"] = safe_clean_str(getnattr(item.find("h4"), 'text'))
        dates = item.find_all("abbr")
        if len(dates) > 1:
            dict_item["start_date"] = dates[0].get('title')
            dict_item["end_date"] = dates[1].get('title')
        if len(dates) == 1 and not "Present" in item:
            dict_item["graduation_date"] = dates[0].get('title')
        if len(dates) == 1 and "Present" in item:
            dict_item["start_date"] = dates[0].get('title')
            dict_item["end_date"] = "Present"

        dict_item["description"] = safe_clean_str(getnattr(item.find("p.description"), 'text'))
        schools.append(dict_item)
    return schools

def find_background_schools(background_schools):
    schools = []
    for item in background_schools.find_all("div"):
        dict_item = {}
        dict_item["college"] = safe_clean_str(getnattr(item.find("h4"), 'text'))
        degrees = item.find_all("h5")
        if len(degrees) == 2:
            dict_item["degree"] = safe_clean_str(getnattr(degrees[1], 'text'))
        if len(degrees) == 1:
            dict_item["degree"] = safe_clean_str(getnattr(degrees[0], 'text'))
        dates = item.find_all("time")
        if len(dates) > 1:
            dict_item["start_date"] = getnattr(dates[0], 'text')
            dict_item["end_date"] = safe_clean_str(getnattr(dates[1], 'text').encode('ascii', 'ignore'))
        if len(dates) == 1 and not "Present" in item:
            dict_item["graduation_date"] = getnattr(dates[0], 'text')
        if len(dates) == 1 and "Present" in item:
            dict_item["start_date"] = getnattr(dates[0], 'text')
            dict_item["end_date"] = "Present"

        dict_item["description"] = safe_clean_str(getnattr(item.find("p.description"), 'text'))
        schools.append(dict_item)
    return schools

def find_schools(soup):
    schools = []

    #Linkedin has two different kinds of public pages HTML
    profile_schools = soup.find(id="profile-education")
    background_schools = soup.find(id="background-education")
    if profile_schools:
        schools = find_profile_schools(profile_schools)
    if background_schools:
        schools = find_background_schools(background_schools)
    return schools

def parse_html(html):
    #TODO put back in 'lxml'
    soup = BeautifulSoup(html, 'lxml')

    full_name = None
    full_name_el = soup.find(class_='full-name')
    if full_name_el:
        full_name = full_name_el.text.strip()
    try:
        div = soup.find("div", id=member_re)
        linkedin_id = div.get("id").split("-")[1]
        if len(linkedin_id) < 3:
            linkedin_index = str(soup).find("newTrkInfo='") + 12
            end_index = str(soup)[linkedin_index:].find("'")
            linkedin_id = str(soup)[linkedin_index:linkedin_index + end_index].replace(",", "")
    except:
        try:
            linkedin_index = str(soup).find("newTrkInfo='") + 12
            end_index = str(soup)[linkedin_index:].find("'")
            linkedin_id = str(soup)[linkedin_index:linkedin_index+end_index].replace(",", "")
        except:
            linkedin_id = None

    try:
        all_dd = soup.find("div", id='location').find_all("dd")
        location = all_dd[0].text
        industry = all_dd[1].text
    except:
        try:
            location = soup.find("span", {'class': 'locality'}).text
            industry = soup.find("dd", {'class': "industry"}).text
        except:
            location = None
            industry = None

    location = safe_clean_str(location)
    industry = safe_clean_str(industry)

    try:
        connections = soup.find("div", {"class": "member-connections"}).text.split("connections")[0]
    except:
        try:
            connections = soup.find("dd", {'class': "overview-connections"}).text
        except:
            connections = None


    experiences = find_jobs(soup)

    schools = find_schools(soup)

    skills = [e.text for e in soup.find_all("li", {'class': 'endorse-item'})]
    people = get_linked_profiles(html)

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
    parser.add_argument('--noresults')
    args = parser.parse_args()
    debug()
