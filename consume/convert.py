import json
import re
import argparse
import urlparse
import logging

from bs4 import BeautifulSoup

logging.basicConfig(filename="convert.txt", level=logging.INFO)
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

def find_jobs(soup):
    jobs = []
    try:
        for item in soup.find(id="profile-experience").find_all("div", {"class": "position"}):
            dict_item = {}
            dict_item["title"] = safe_clean_str(getnattr(item.find("h3"), 'text'))
            dict_item["company"] = safe_clean_str(getnattr(item.find("h4"), 'text'))
            dates = item.find_all("abbr")
            if len(dates) > 1:
                dict_item["start_date"] = getnattr(dates[0], 'text')
                dict_item["end_date"] = getnattr(dates[1], 'text')
            if len(dates) == 1:
                dict_item["start_date"] = getnattr(dates[0], 'text')
                dict_item["end_date"] = "Present"

            dict_item["description"] = safe_clean_str(getnattr(item.find("p.description"), 'text'))
            jobs.append(dict_item)
        return jobs
    except Exception, e:
        pass

    try:
        for item in soup.find(id="background-experience").find_all("div"):
            dict_item = {}
            dict_item["title"] = safe_clean_str(getnattr(item.find("h4"), 'text'))
            dict_item["company"] = safe_clean_str(getnattr(item.find("h5"), 'text'))
            dict_item["description"] = safe_clean_str(getnattr(item.find(".description"), 'text'))
            dates = item.find_all("time")
            if len(dates) > 1:
                dict_item["start_date"] = getnattr(dates[0], 'text')
                dict_item["end_date"] = getnattr(dates[1], 'text')
            if len(dates) == 1:
                dict_item["start_date"] = getnattr(dates[0], 'text')
                dict_item["end_date"] = "Present"

            jobs.append(dict_item)
        return jobs
    except Exception, e:
        pass

    return jobs

def find_schools(soup):
    schools = []
    try:
        for item in soup.find(id="profile-education").find_all("div", {"class": "position"}):
            dict_item = {}
            dict_item["college"] = safe_clean_str(getnattr(item.find("h3"), 'text'))
            dict_item["degree"] = safe_clean_str(getnattr(item.find("h4"), 'text'))
            dates = item.find_all("abbr")
            if len(dates) > 1:
                dict_item["start_date"] = getnattr(dates[0], 'text')
                dict_item["end_date"] = getnattr(dates[1], 'text')
            if len(dates) == 1 and not "Present" in item:
                dict_item["graduation_date"] = getnattr(dates[0], 'text')
            if len(dates) == 1 and "Present" in item:
                dict_item["start_date"] = getnattr(dates[0], 'text')
                dict_item["end_date"] = "Present"

            dict_item["description"] = safe_clean_str(getnattr(item.find("p.description"), 'text'))
            schools.append(dict_item)
        return schools
    except Exception, e:
        pass

    try:
        for item in soup.find(id="background-education").find_all("div"):
            dict_item = {}
            dict_item["college"] = safe_clean_str(getnattr(item.find("h4"), 'text'))
            dict_item["degree"] = safe_clean_str(getnattr(item.find("h5"), 'text'))
            dates = item.find_all("time")
            if len(dates) > 1:
                dict_item["start_date"] = getnattr(dates[0], 'text')
                dict_item["end_date"] = getnattr(dates[1], 'text')
            if len(dates) == 1 and not "Present" in item:
                dict_item["graduation_date"] = getnattr(dates[0], 'text')
            if len(dates) == 1 and "Present" in item:
                dict_item["start_date"] = getnattr(dates[0], 'text')
                dict_item["end_date"] = "Present"

            dict_item["description"] = safe_clean_str(getnattr(item.find("p.description"), 'text'))
            schools.append(dict_item)
        return schools
    except Exception, e:
        pass

    return schools

def parse_html(html):
    soup = BeautifulSoup(html, 'lxml')

    full_name = None
    full_name_el = soup.find(class_='full-name')
    if full_name_el:
        full_name = full_name_el.text.strip()
    try:
        div = soup.find("div", id=member_re)
        linkedin_id = div.get("id").split("-")[1]
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
    main()
