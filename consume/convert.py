import json
import boto
import sys
import lxml.html
from lxml import etree
import os
import re
import argparse
import urlparse
import logging
import StringIO
import csv
from boto.s3.key import Key

#from bs4 import BeautifulSoup, SoupStrainer

profile_re = re.compile('^https?://www.linkedin.com/pub/.*/.*/.*')
member_re  = re.compile("member-")

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

def s3():
    s3conn = boto.connect_s3(os.environ["AWS_ACCESS_KEY_ID"], os.environ["AWS_SECRET_ACCESS_KEY"])
    write_bucket = s3conn.get_bucket('advisorconnect-bigfiles')
    read_bucket = s3conn.get_bucket('arachid-results')


def convert(filename, writefile):
    file = open(filename, 'r').read()
    html = json.loads(file).get("content")
    result = parse_html(html)
    writefile.write(unicode(json.dumps(result)).decode("utf-8", "ignore"))
    return True

def main():
    os.chdir("data")
    for filename in os.listdir(os.getcwd()):
        file = open(filename, 'r').read()
        html = json.loads(file).get("content")
        results =  parse_html(html)
        print results
        #print "File:{0}, Jobs: {1}, Schools:{2}".format(filename,\
        #        len(results.get("experiences", 0)),
        #        len(results.get("schools", 0)))

def debug():
    #file = open("data/http:www.linkedin.compubzachary-kowalski37372872", 'r').read()
    file = open("data/http:www.linkedin.compubalbie-solis1ab8b34", 'r').read()
    html = json.loads(file).get("content")
    return parse_html(html)

def get_projects(raw_html):
    projects = []
    for project in raw_html.xpath("//div[@class='background-projects']/div/div"):
        dict_item = {}
        dates = project.xpath("./span/time")
        if len(dates) > 1:
            dict_item["start_date"] = dates[0].text_content()
            dict_item["end_date"] = dates[1].text_content()
        if len(dates) == 1:
            dict_item["start_date"] = dates[0].text_content()
        description = project.xpath("./p")
        if len(description)> 0:
            dict_item['description'] = description[0].text_content()
        title = project.xpath(".//h4/a/span")
        if len(title) > 0:
            dict_item['title'] = title[0].text_content()
        dict_item['other_people'] = raw_html.xpath("//div[@class='background-projects']/div/div")[0].xpath(".//dd/ul/li/a/@href")
        projects.append(dict_item)
    return projects

#TODO: parse languages

#TODO: fix image parsing
def get_groups(raw_html):
    try:
        return [{"image_url": p.xpath("./a/img")[0].attrib.get("src"), "group_id": p.xpath("./a")[1].attrib.get("href").split("gid=")[1].split("&")[0], "name":p.xpath("./a")[1].text_content()} for p in raw_html.xpath("//p[@class='groups-name']")]
    except:
        return []

def parse_images(raw_html):
    images = raw_html.xpath("//img")
    images = [img.get("src") for img in images]
    for img in images:
        if "mpr/shrink_200_200" in img:
            return img
        if "mpr/shrink_500_500" in img:
            return img.replace("500_500", "200_200")
    return None

def find_images():
    count = 0
    exists = 0
    os.chdir("data")
    for filename in os.listdir(os.getcwd()):
        count += 1
        file = open(filename, 'r').read()
        html = json.loads(file).get("content")
        if parse_images(html):
            exists += 1
    print "Attempted: {} Exists: {}".format(count, exists)


def is_profile_link(link):

    if link and re.match(profile_re, link):
        return True
    return False

def get_linked_profiles(raw_html):
    linkedin_profiles = [a.attrib.get("href", "").split("?")[0] for a in \
            raw_html.xpath("//div[@class='insights-browse-map']/ul/li/a")]
    return list(set(linkedin_profiles))

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
            company_link = item.xpath(".//a/@href")
            if len(company_link) > 1:
                dict_item["company_id"] = company_link[1].split("?")[0].split("company/")[1]
        dates = item.findall(".//abbr")
        if len(dates) > 1:
            dict_item["start_date"] = dates[0].get('title')
            dict_item["end_date"] = dates[1].get('title')
        if len(dates) == 1:
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
            try:
                dict_item["company_id"] = item.xpath(".//h5/a/@href")[0].split("?")[0].split("company/")[1]
                if len(item.xpath(".//h5/a/img/@data-li-src")): dict_item["company_image_url"] = item.xpath(".//h5/a/img/@data-li-src")[0]
            except:
                pass
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
            links = college.xpath(".//a/@href")
            if len(links) > 0:
                dict_item["college_id"] = links[0].split("?")\
                        [0].split("edu/")[1].split("-")[-1]
        degree = item.find(".//h4")
        if degree is not None:
            dict_item["degree"] = safe_clean_str(degree.text_content())
        dates = item.findall(".//abbr")
        if len(dates) > 1:
            dict_item["start_date"] = dates[0].get('title')
            dict_item["end_date"] = dates[1].get('title')

        present = "Present" in etree.tostring(item, pretty_print=True)
        if len(dates) == 1 and not present:
            dict_item["end_date"] = dates[0].get('title')
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
            entity = item.find(".//h5/[@class='education-logo']")
            if entity is not None:
                try:
                    dict_item["college_id"] = entity.xpath(".//span/@data-li-url")[0].split("id=")[1].split("&")[0]
                    dict_item["college_image_url"] = entity.find(".//img").xpath(".//@src")[0]
                except:
                    pass
        degrees = item.findall(".//h5")
        if len(degrees) == 2:
            dict_item["degree"] = safe_clean_str(degrees[1].text_content())
        if len(degrees) == 1:
            dict_item["degree"] = safe_clean_str(degrees[0].text_content())
        dates = item.findall(".//time")
        if len(dates) > 1:
            dict_item["start_date"] = safe_clean_str(dates[0].text_content())
            dict_item["end_date"] = safe_clean_str(dates[1].text_content().encode('ascii', 'ignore'))

        present = "Present" in etree.tostring(item, pretty_print=True)
        if len(dates) == 1 and not present:
            dict_item["end_date"] = dates[0].text_content()
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

    linkedin_id = None
    linkedin_index = html.find("newTrkInfo=") + 10
    if linkedin_index == 9: linkedin_index = html.find(",memberId:") + 10
    linkedin_id = html[linkedin_index:].replace("'",'"').split('"')[1].split(",")[0]

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

    try:
        image = raw_html.xpath(".//div[@class='profile-picture']/a/img/@src")[0]
    except:
        image = None


    location = safe_clean_str(location)
    industry = safe_clean_str(industry)

    connections = None
    #raw_html.xpath("//div[@class='insights-browse-map']/ul/li/")
    try:
        connections = raw_html.xpath("//div[@class='member-connections']")[0].text_content()
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
        schools = find_background_schools(raw_html)


    skills = [e.text_content() for e in raw_html.xpath("//ul[@class='skills-section compact-view']/li") if "jsControl" not in e.text_content()]
    people = get_linked_profiles(raw_html)
    groups = get_groups(raw_html)
    projects = get_projects(raw_html)
    
    source_url_regex = re.compile(r'(?<="X-FS-Origin-Request":").+(?=",)')
    source_url_match = re.search(source_url_regex,html) 
    if source_url_match is not None:
        source_url = "http://www.linkedin.com" + source_url_match.group(0)
    else:
        source_url = None

    if full_name is None or len(full_name)==0: 
        success = False
        complete = False
    else: 
        success = True
        complete = html.find("background_view") > -1
    return {
        'image': image,
        'linkedin_id': linkedin_id,
        'full_name': full_name,
        'schools': schools,
        'experiences': experiences,
        'skills': skills,
        'people': people,
        'connections': connections,
        'location': location,
        'industry': industry,
        "groups": groups,
        "projects": projects,
        "success": success,
        "complete": complete,
        "urls":people,
        "source_url": source_url
    }


def url_to_key(url):
    return url.replace('/', '')

def info_is_valid(info):
    return info.get('full_name') and \
           info.get('linkedin_id')


def get_info_for_url(url):
    #key = Key(read_bucket)
    #key.key = url_to_key(url)
    #data = json.loads(key.get_contents_as_string())
    #info = parse_html(data['content'])
    file = open("data/" + url_to_key(url), 'r').read()
    html = json.loads(file).get("content")
    info = parse_html(html)
    return info

def uu(str):
    if str:
        return str.encode("ascii", "ignore").decode("utf-8")
    return None

def write_to_s3(filename):
    file = open(filename)
    for line in file:
        try:
            info = get_info_for_url(line.strip("\n"))
        except Exception, e:
            logger.debug('error processing {}, {}'.format(line, e))
            pass
        else:
            if info_is_valid(info):
                person_file = StringIO.StringIO()
                person_writer = csv.writer(person_file, delimiter="\t")
                person = [info.get("linkedin_id"),
                            info.get("image_url"),
                            uu(info.get("full_name")),
                            uu(",".join(info.get("skills"))),
                            uu(",".join(info.get("people"))),
                            uu(info.get("connections")),
                            uu(info.get("location")),
                            uu(info.get("industry")),
                            uu(str(info.get("groups"))),
                            uu(str(info.get("projects")))]
                person_writer.writerow(person)

                educations = [[info.get("linkedin_id"),
                            uu(school.get("college")),
                            school.get("college_id"),
                            school.get("college_image_url"),
                            uu(school.get("start_date")),
                            uu(school.get("end_date")),
                            uu(school.get("degree")),
                            uu(school.get("description", "").replace("\n", ""))] for school in info.get("schools")]
                education_file = StringIO.StringIO()
                education_writer = csv.writer(education_file, delimiter="\t")
                education_writer.writerows(educations)

                jobs = [[info.get("linkedin_id"),
                            uu(job.get("company")),
                            job.get("company_id"),
                            job.get("company_image_url"),
                            uu(job.get("start_date")),
                            uu(job.get("end_date")),
                            uu(job.get("title")),
                            uu(job.get("description", "").replace("\n", "")),
                            uu(job.get("location"))] for job in info.get("experiences")]
                job_file = StringIO.StringIO()
                job_writer = csv.writer(job_file, delimiter="\t")
                job_writer.writerows(jobs)

                prospect_key = Key(write_bucket)
                educations_key = Key(write_bucket)
                jobs_key = Key(write_bucket)

                prospect_key.key = "processed_data/prospects/{}.csv".format(line)
                prospect_key.set_contents_from_string(person_file.getvalue())

                educations_key.key = "processed_data/educations/{}.csv".format(line)
                educations_key.set_contents_from_string(education_file.getvalue())

                jobs_key.key = "processed_data/jobs/{}.csv".format(line)
                jobs_key.set_contents_from_string(job_file.getvalue())

                logger.debug('succesfully processed {}'.format(line))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--benchmark', action='store_true')
    parser.add_argument('--images', action='store_true')
    parser.add_argument('--linkedin', action='store')
    args = parser.parse_args()

    if args.benchmark:
        import timeit
        print(timeit.timeit("debug()", setup="from __main__ import debug",
            number=10000))
    elif args.images:
        find_images()
    else:
        write_to_s3("names.txt")


