try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
import json
import boto
import sys
import lxml.html
from lxml import etree
import os
import re
import pandas
import StringIO
import csv, shutil
from boto.s3.key import Key
from mrjob.job import MRJob
from sys import stderr
import boto.s3.connection
import subprocess
import multiprocessing 
import requests
from boto.s3.key import Key
import multiprocessing 
from multiprocessing.managers import SyncManager
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask

profile_re = re.compile('^https?://www.linkedin.com/pub/.*/.*/.*')
member_re  = re.compile("member-")

write_bucket_name = 'advisorconnect-bigfiles'
read_bucket_name = 'arachid-results'
list_bucket_name = 'mrjob-lists'

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://arachnid:devious8ob8@arachnid.cc540uqgo1bi.us-east-1.rds.amazonaws.com:5432/arachnid'
SQL = "select max(id) from prospect where linkedin_id='%s';"
writefiles = ["education", "job", "person"]
good_files = ["companies","schools"]

class processLinkedIn(MRJob):

    def mapper(self, _, filename):

        print "Just started mapper function"
        try:
            cpu_count = multiprocessing.cpu_count()
            mgr = SyncManager(('127.0.0.1',0))
            mgr.start()
            Global = mgr.Namespace()
            Global.part_num = int(re.sub("[^0-9]","",filename)) + 1
        except:
            pass
            print "mapper failed before ANYTHING happened..."
            yield "none", {}
            return 

        for f in writefiles + good_files:
            try:
                os.remove(f)
            except OSError:
                pass

        try:
            s3conn = boto.connect_s3()
            list_bucket = s3conn.get_bucket(list_bucket_name)  
            key = Key(list_bucket)
            key.key = filename
            key.get_contents_to_filename(filename)
            pool = multiprocessing.Pool(cpu_count*5)
            df = pandas.read_csv(filename, delimiter="\t", names=["num", "key","prospect_id"], header=None)
            #file_list = df["key"].tolist()
            file_list = map(list, df.values)            
        except:
            pass
            print "mapper failed at part_num " + str(Global.part_num)
            yield "none", {}
            return

        print "got the list of files to process from s3"

        results = pool.map(parseFile, file_list)
        for result in results:
            sys.stdout.write(result)

        print "processed files"

        pool = multiprocessing.Pool(len(writefiles)+len(good_files))
        params = []
        for writefile in writefiles:
            param = (writefile, Global)
            params.append(param)
        results = pool.map(upload, params)

        print "uploaded results"

        for result in results:
            print result

        results_tuples = pool.map(make_dicts, good_files)

        print "made dicts"

        for result_tuple in results_tuples:
            print "for part num " + str(Global.part_num) + ", dict type " + result_tuple[0] + " yielded " + str(len(result_tuple[1])) + " items"
            yield result_tuple[0], result_tuple[1]

    def combiner(self, dict_type, dicts):
        bigger_dict = {}

        for mini_dict in dicts:
            try:
                bigger_dict.update(mini_dict)
            except:
                pass

        print "for combiner, dict type " + dict_type + " yielded " + str(len(bigger_dict))
        yield dict_type, bigger_dict

    def reducer(self, dict_type, dicts):
        bigger_dict = {}

        s3conn = boto.connect_s3()
        write_bucket = s3conn.get_bucket(write_bucket_name)   

        for mini_dict in dicts:
            try:
                bigger_dict.update(mini_dict)
            except:
                pass
        try:
            df = pandas.DataFrame.from_dict(bigger_dict, orient='index')
            df.to_csv(dict_type, sep="\t", encoding='utf-8', header=False)
            k = Key(write_bucket)
            k.key = "processed/" + dict_type + ".txt"
            k.set_contents_from_filename(dict_type)
        except:
            print "in reducer, error uploading dict type " + dict_type
            pass

        print "for reducer, dict type " + dict_type + " yielded " + str(len(bigger_dict)) 
        yield dict_type, bigger_dict

def upload(param):
    name = param[0] 
    part_num = param[1].part_num
    try:
        s3conn = boto.connect_s3()
        write_bucket = s3conn.get_bucket(write_bucket_name)   
        uploads = write_bucket.get_all_multipart_uploads() 
        num = writefiles.index(name)
        mp = uploads[num]
        _upload_part(mp, name, part_num)
        return "multipart upload for part num " + str(part_num) + " success"
    except:
        pass
        return "multipart upload for part num " + str(part_num) + " failed"

def make_dicts(type):
    try:
        df = pandas.read_csv(type, delimiter="\t", header=None, names=["key","value"])
        keys = df["key"].tolist()
        values = df["value"].tolist()
        return (type, dict(zip(keys,values)))
    except:
        pass
    return (type, {})

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

def is_profile_link(link):

    if link and re.match(profile_re, link):
        return True
    return False

def info_is_valid(info):
    return info.get('full_name') and \
           info.get('linkedin_id')

def get_linked_profiles(raw_html):
    linkedin_profiles = [a.attrib.get("href", "").split("?")[0] for a in \
            raw_html.xpath("//div[@class='insights-browse-map']/ul/li/a")]
    return list(set(linkedin_profiles))

def safe_clean_str(s):
    if s:
        return re.sub("\n","", s.strip())
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

def calculate_salary(title, location=None):
    '''
    headers = {
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1'
            }
    if location is not None:
        url =  "http://www.indeed.com/salary?q1=%s&l1=#%s" % (title,location)
    else:
        url =  "http://www.indeed.com/salary?q1=%s" % (title)        
    try:
        response = requests.get(url, headers=headers)
        clean = lxml.html.fromstring(response.content)
        salary = clean.xpath("//span[@class='salary']")[0].text
        return salary
    except Exception, err:
        pass
    '''    
    return None

def find_profile_jobs(raw_html):
    jobs = []
    good_titles = {}
    profile_jobs = raw_html.xpath("//div[@id='profile-experience']")[0]
    for item in profile_jobs.xpath(".//div[contains(@class, 'position ')]"):
        dict_item = {}
        title = item.find(".//h3")
        title_str = None
        location_str = None
        if title is not None:
            title_str = safe_clean_str(title.text_content())
            dict_item["title"] = title_str
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
            location_str = safe_clean_str(location[0].text_content())
            dict_item['location'] = location_str
        description = item.xpath(".//p[contains(@class, ' description ')]")
        if len(description) > 0:
            dict_item["description"] = safe_clean_str(description[0].text_content())
        if title_str is not None:
            dict_item["title_salary"] = calculate_salary(title_str)
            if dict_item["title_salary"] is not None: good_titles.update({hash(title_str):uu(title_str)})
        jobs.append(dict_item)
    return jobs, good_titles

def find_background_jobs(raw_html):
    jobs = []
    good_companies = {}
    good_titles = {}
    background_jobs = raw_html.xpath("//div[@id='background-experience']/div")
    for item in background_jobs:
        dict_item = {}
        title = item.find(".//h4")
        title_str = None
        location_str = None
        if title is not None:
            title_str = safe_clean_str(title.text_content())
            dict_item["title"] = title_str
        company = item.findall(".//h5")
        if len(company) == 2:
            dict_item["company"] = safe_clean_str(company[1].text_content())
            dict_item["company_id"] = item.xpath(".//h5/a/@href")[0].split("?")[0].split("company/")[1]
            dict_item["company_image_url"] = item.xpath(".//h5/a/img/@src")[0]
            if dict_item["company_image_url"] is not None: good_companies.update({dict_item["company_id"]:uu(dict_item["company"])})
        else:
            dict_item["company"] = safe_clean_str(company[0].text_content())
        location = item.xpath(".//span[@class='locality']")
        if len(location) > 0:
            location_str = safe_clean_str(location[0].text_content())
            dict_item['location'] = location_str
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
        if title_str is not None:
            dict_item["title_salary"] = calculate_salary(title_str)
            if dict_item["title_salary"] is not None: good_titles.update({hash(title_str):uu(title_str)})
        jobs.append(dict_item)
    return jobs, good_titles, good_companies


def find_profile_schools(raw_html):
    schools = []
    good_degrees = {}
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
            dict_item["degree_salary"] = calculate_salary(dict_item["degree"])
            if dict_item["degree_salary"] is not None: good_degrees.update({hash(dict_item["degree"]):uu(dict_item["degree"])})
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
    return schools, good_degrees

def find_background_schools(raw_html):
    schools = []
    good_degrees = {}
    good_schools = {}
    background_schools = raw_html.xpath("//div[@id='background-education']/div")
    for item in background_schools:
        dict_item = {}
        college = item.find(".//h4")
        if college is not None:
            dict_item["college"] = safe_clean_str(college.text_content())
            links = item.xpath(".//a/@href")
            if len(links) > 0:
                dict_item["college_id"] = links[0].split("id=")[1].split("&")[0]
            college_image = item.xpath(".//img/@src")
            if len(college_image) > 0:
                dict_item["college_image_url"] = college_image[0]
                good_schools.update({dict_item["college_id"]:dict_item["college"]})
        degrees = item.findall(".//h5")
        if len(degrees) == 2:
            dict_item["degree"] = safe_clean_str(degrees[1].text_content())
        if len(degrees) == 1:
            dict_item["degree"] = safe_clean_str(degrees[0].text_content())
        if len(degrees)>0:
            dict_item["degree_salary"] = calculate_salary(dict_item["degree"])
            if dict_item["degree_salary"] is not None: good_degrees.update({hash(dict_item["degree"]):uu(dict_item["degree"])})            
        dates = item.findall("time")
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
    return schools, good_degrees, good_schools


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

    try:
        image = parse_images(raw_html)
    except:
        image = None


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
    good_titles = {}
    good_degrees = {}
    good_companies = {}
    good_schools = {}
    if len(raw_html.xpath("//div[@id='profile-experience']")) > 0:
        experiences, good_titles = find_profile_jobs(raw_html)

    if len(raw_html.xpath("//div[@id='background-experience']")) > 0:
        experiences, good_titles, good_companies = find_background_jobs(raw_html)

    school_type = None
    if len(raw_html.xpath("//div[@id='profile-education']")) > 0:
        schools, good_degrees = find_profile_schools(raw_html)

    if len(raw_html.xpath("//div[@id='background-education']")) > 0:
        schools, good_degrees, good_schools = find_background_schools(raw_html)


    skills = [e.text_content() for e in raw_html.xpath("//ul[@class='skills-section compact-view']/li") if "jsControl" not in e.text_content()]
    people = get_linked_profiles(raw_html)
    groups = get_groups(raw_html)
    projects = get_projects(raw_html)

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
        "good_titles": good_titles,
        "good_degrees": good_degrees,
        "good_companies": good_companies, 
        "good_schools": good_schools        
    }


def url_to_key(url):
    return url.replace('/', '')

def get_info_for_url(url):
    s3conn = boto.connect_s3()
    read_bucket = s3conn.get_bucket(read_bucket_name)
    key = Key(read_bucket)
    key.key = url_to_key(url)
    data = json.loads(key.get_contents_as_string())
    info = parse_html(data['content'])
    return info

def uu(str):
    if str:
        return str.encode("ascii", "ignore").decode("utf-8")
    return None

def parseFile(row):
    rec_num = None
    try:
        rec_num = row[0]
        s3_key = row[1]
        prospect_id = row[2]
    except:
        pass
        return "parseFile for record number " + str(rec_num) + " failed"
    try:
        info = get_info_for_url(s3_key.strip("\n"))
    except Exception, e:
        pass
        return "parseFile for record number " + str(rec_num) + ", key " + s3_key + " failed"
    if not info_is_valid(info): return
    linkedin_id = info.get("linkedin_id")

    if prospect_id is None:
        try:
            db = SQLAlchemy(app)
            session = db.session
            prospect_id = session.execute(SQL % (linkedin_id)).first()[0]
        except:
            pass
            return "parseFile for record number " + str(rec_num) + ", key " + s3_key + " failed"

    try:
        person = [prospect_id, linkedin_id, 
                    info.get("image_url"),
                    uu(info.get("full_name")),
                    uu(",".join(info.get("skills"))),
                    uu(",".join(info.get("people"))),
                    uu(info.get("connections")),
                    uu(info.get("location")),
                    uu(info.get("industry")),
                    uu(str(info.get("groups"))),
                    uu(str(info.get("projects")))]

        with open(writefiles[2], 'ab') as person_file:
            person_writer = csv.writer(person_file, delimiter="\t")                        
            person_writer.writerow(person)
            person_file.close()
        
        educations = [[prospect_id, linkedin_id, 
                    uu(school.get("college")),
                    school.get("college_id"),
                    school.get("college_image_url"),
                    uu(school.get("start_date")),
                    uu(school.get("end_date")),
                    uu(school.get("degree")),
                    uu(school.get("description", "").replace("\n", ""))] for school in info.get("schools")]

        with open(writefiles[0], 'ab') as education_file:
            education_writer = csv.writer(education_file, delimiter="\t")      
            education_writer.writerows(educations)
            education_file.close()

        
        jobs = [[prospect_id, linkedin_id, 
                    uu(experience.get("company")),
                    experience.get("company_id"),
                    experience.get("company_image_url"),
                    uu(experience.get("start_date")),
                    uu(experience.get("end_date")),
                    uu(experience.get("title")),
                    uu(experience.get("description", "").replace("\n", "")),
                    uu(experience.get("location"))] for experience in info.get("experiences")]
        
        with open(writefiles[1], 'ab') as job_file:
            job_writer = csv.writer(job_file, delimiter="\t")    
            job_writer.writerows(jobs)
            job_file.close()

        with open("companies", 'ab') as companies_file:
            for id, name in info.get("good_companies").iteritems():
                if name is not None and len(name)>0:
                    companies_file.write(id + "\t" + uu(name) + "\n")
            companies_file.close()

        with open("schools", 'ab') as schools_file:
            for id, name in info.get("good_schools").iteritems():
                if name is not None and len(name)>0:
                    schools_file.write(id + "\t" + uu(name) + "\n")
            schools_file.close()
        return "parseFile for record number " + str(rec_num) + ", key " + s3_key + " successful"
    except:
        pass
        return "parseFile for record number " + str(rec_num) + ", key " + s3_key + " failed"

def _upload_part(mp, filename, part_num, amount_of_retries=4):
    """
    Uploads a part with retries.
    """ 
    headers = {'Content-Type': "text/tab-separated-values"}
    file = open(filename,'rb')

    def _upload(retries_left=amount_of_retries):
        try:
            file.seek(0)
            mp.upload_part_from_file(fp=file, part_num=part_num, headers=headers)
        except Exception, exc:
            if retries_left:

                _upload(retries_left=retries_left - 1)
            else:
                raise exc

    _upload()

if __name__ == '__main__':
    processLinkedIn.run()