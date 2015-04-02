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
import logging
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

logger = logging.getLogger('consumer')
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

logfile=stderr  

write_bucket = 'advisorconnect-bigfiles'
read_bucket = 'arachid-results'
list_bucket = 'mrjob-lists'

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DB_URL"]
db = SQLAlchemy(app)
SQL = "select max(id) from prospect where linkedin_id='%s';"

class processLinkedIn(MRJob):

    def mapper(self, _, filename):

        cpu_count = multiprocessing.cpu_count()
        mgr = SyncManager(('127.0.0.1',0))
        mgr.start()

        Global = mgr.Namespace()
        Global.part_num = int(re.sub("[^0-9]","",filename)) + 1
        Global.write_bucket = write_bucket
        Global.read_bucket = read_bucket

        writefiles = mgr.list(["education", "job", "person"])
        for writefile in writefiles:
            try:
                os.remove(writefile)
            except OSError:
                pass
        
        '''
        good_titles_dict = mgr.dict()
        good_degrees_dict = mgr.dict()
        good_schools_dict = mgr.dict()
        good_companies_dict = mgr.dict()
        '''
        educations_lock = mgr.Lock()
        jobs_lock = mgr.Lock()
        prospects_lock = mgr.Lock()

        s3conn = boto.connect_s3()
        bucket = s3conn.get_bucket(list_bucket)  
        key = Key(bucket)
        key.key = filename
        key.get_contents_to_filename(filename)

        pool = multiprocessing.Pool(cpu_count*5)
        df = pandas.read_csv(filename, delimiter="\t", names=["num", "key"])
        for index, row in df.iterrows():
            file_to_parse = row["key"]
            '''
            pool.apply_async(parseFile, (file_to_parse, Global, writefiles, educations_lock, jobs_lock, prospects_lock, good_degrees_dict, good_schools_dict, good_titles_dict, good_companies_dict))
            '''
            pool.apply_async(parseFile, (file_to_parse, Global, writefiles))
        pool.close()
        pool.join()

        pool = multiprocessing.Pool(len(writefiles))
        for writefile in writefiles:
            pool.apply_async(upload, (writefile, Global, writefiles))
        pool.close()
        pool.join()
        '''
        yield "good_titles_dict", good_titles_dict
        yield "good_schools_dict",good_schools_dict
        yield "good_companies_dict",good_companies_dict
        yield "good_degrees_dict",good_degrees_dict
        '''
    '''    
    def combiner(self, dict_type, dicts):
        bigger_dict = {}
        for mini_dict in dicts:
            bigger_dict.update(mini_dict)
        yield dict_type, bigger_dict
    


    def reducer(self, dict_type, dicts):
        s3conn = boto.connect_s3()
        write_bucket = s3conn.get_bucket(write_bucket)   

        bigger_dict = {}
        for mini_dict in dicts:
            bigger_dict.update(mini_dict)
        
        df = pandas.DataFrame.from_dict(bigger_dict, orient='index')
        df.to_csv(dict_type, sep="\t", encoding='utf-8', header=False)
        k = Key(write_bucket)
        k.key = "processed/" + dict_type + ".txt"
        k.set_contents_from_filename(dict_type)
    
    '''
    
def upload(name, Global, writefiles):
    cmd = "cat $(ls -t " + name + "* ) > _" + name
    subprocess.call(cmd, shell=True)

    s3conn = boto.connect_s3()
    write_bucket = s3conn.get_bucket(Global.write_bucket)   
    uploads = write_bucket.get_all_multipart_uploads() 
    num = writefiles.index(name)
    mp = uploads[num]
    _upload_part(mp, "_"+name, Global.part_num)

    cmd = "rm " + name + "*" 
    subprocess.call(cmd, shell=True)

def convert(filename, writefile):
    file = open(filename, 'r').read()
    html = json.loads(file).get("content")
    result = parse_html(html)
    writefile.write(unicode(json.dumps(result)).decode("utf-8", "ignore"))
    return True


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

def get_info_for_url(url, read_bucket):
    s3conn = boto.connect_s3()
    read_bucket = s3conn.get_bucket(read_bucket)
    key = Key(read_bucket)
    key.key = url_to_key(url)
    data = json.loads(key.get_contents_as_string())
    info = parse_html(data['content'])
    return info

def uu(str):
    if str:
        return str.encode("ascii", "ignore").decode("utf-8")
    return None

def parseFile(s3_key, Global, writefiles):
    try:
        info = get_info_for_url(s3_key.strip("\n"),Global.read_bucket)
    except Exception, e:
        logger.debug('error processing {}, {}'.format(s3_key, e))
        pass
    else:
        if not info_is_valid(info): return
        linkedin_id = info.get("linkedin_id")
        prospect_id = None

        
        session = db.session
        try:
            prospect_id = session.execute(SQL % (linkedin_id)).first()[0]
        except:
            pass
            

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
        
        
        #prospects_lock.acquire()
        with open(writefiles[2] + linkedin_id, 'wb') as person_file:
            person_writer = csv.writer(person_file, delimiter="\t")                        
            person_writer.writerow(person)
            person_file.close()
        #prospects_lock.release()
        
        educations = [[prospect_id, linkedin_id, 
                    uu(school.get("college")),
                    school.get("college_id"),
                    school.get("college_image_url"),
                    uu(school.get("start_date")),
                    uu(school.get("end_date")),
                    uu(school.get("degree")),
                    uu(school.get("description", "").replace("\n", ""))] for school in info.get("schools")]
        

        #educations_lock.acquire()
        with open(writefiles[0]+linkedin_id, 'wb') as education_file:
            education_writer = csv.writer(education_file, delimiter="\t")      
            education_writer.writerows(educations)
            education_file.close()
        #educations_lock.release()
        
        
        jobs = [[prospect_id, linkedin_id, 
                    uu(experience.get("company")),
                    experience.get("company_id"),
                    experience.get("company_image_url"),
                    uu(experience.get("start_date")),
                    uu(experience.get("end_date")),
                    uu(experience.get("title")),
                    uu(experience.get("description", "").replace("\n", "")),
                    uu(experience.get("location"))] for experience in info.get("experiences")]
        
        
        #jobs_lock.acquire()
        with open(writefiles[1]+linkedin_id, 'wb') as job_file:
            job_writer = csv.writer(job_file, delimiter="\t")    
            job_writer.writerows(jobs)
            job_file.close()
        #jobs_lock.release()
        
        '''
        good_companies_dict.update(info.get("good_companies"))
        good_schools_dict.update(info.get("good_schools"))
        good_degrees_dict.update(info.get("good_degrees"))
        good_titles_dict.update(info.get("good_titles"))
        '''

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
                logging.info('... Failed uploading part #%d' % part_num)
                raise exc
        else:
            logging.info('... Uploaded part #%d' % part_num)
 
    _upload()

if __name__ == '__main__':
    processLinkedIn.run()