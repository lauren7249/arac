import itertools
import operator
import re
import datetime
import dateutil
import json
from difflib import SequenceMatcher
from random import shuffle
import numpy as np
from constants import profile_re, bloomberg_company_re, school_re, company_re

def uu(str):
    if str:
        return str.encode("ascii", "ignore").decode("utf-8")
    return None

def parse_out(text, startTag, endTag):
    """
    Takes a section of text and finds everything between a start tag and end tag
    in html
    """
    region = ""
    region_start = text.find(startTag)
    if region_start > -1:
        region = text[region_start+len(startTag):]
        region_end = region.find(endTag)
        if region_end > -1:
            region = region[:region_end]
    return region

def get_center(coords, remove_outliers=False):
    """
    We use this to find the center of a bunch of coordinates
    """
    distances = []
    for coord in coords:
        total_distance = 0
        for coord2 in coords:
            total_distance += coord.distance_to(coord2)
        distances.append(total_distance)
    if remove_outliers:
        for i in xrange(len(coords)):
            if distances[i] > np.mean(distances) + np.std(distances):
                coords.remove(coords[i])
    min_total_distance = None
    center = None
    for coord in coords:
        total_distance = 0
        for coord2 in coords:
            total_distance += coord.distance_to(coord2)
        if total_distance<min_total_distance or min_total_distance is None:
            min_total_distance = total_distance
            center = coord
    return center


def most_common(L):
    # get an iterable of (item, iterable) pairs
    SL = sorted((x, i) for i, x in enumerate(L))
    # print 'SL:', SL
    groups = itertools.groupby(SL, key=operator.itemgetter(0))
    # auxiliary function to get "quality" for an item
    def _auxfun(g):
        item, iterable = g
        count = 0
        min_index = len(L)
        for _, where in iterable:
            count += 1
            min_index = min(min_index, where)
            # print 'item %r, count %r, minind %r' % (item, count, min_index)
        return count, -min_index
          # pick the highest-count/earliest item
    try:
        return max(groups, key=_auxfun)[0]
    except:
        return None

def filter_bing_results(results, limit=100, url_regex=".", exclude_terms_from_title=None, include_terms_in_title=None):
    """
    Given a list of bing results, it will filter the results based on a url regex
    """
    filtered = []
    if exclude_terms_from_title: exclude_terms_from_title = re.sub("[^a-z\s]",'',exclude_terms_from_title.lower().strip())
    if include_terms_in_title: include_terms_in_title = re.sub("[^a-z\s]",'',include_terms_in_title.lower().strip())
    for result in results:
        link = result.get("Url")
        if re.search(url_regex,link, re.IGNORECASE):
            title = result.get("Title")
            title_meat = re.sub("[^a-z\s]",'',title.split("|")[0].lower().strip())
            if exclude_terms_from_title:
                ratio = SequenceMatcher(None, title_meat, exclude_terms_from_title.lower().strip()).ratio()
                intersect = set(exclude_terms_from_title.split(" ")) & set(title_meat.split(" "))
                if len(intersect) >= min(2,len(exclude_terms_from_title.split(" "))) or ratio>=0.8:
                    continue
            if include_terms_in_title:
                ratio = SequenceMatcher(None, title_meat, include_terms_in_title.lower().strip()).ratio()
                intersect = set(include_terms_in_title.split(" ")) & set(title_meat.split(" "))
                if len(intersect) < min(2,len(include_terms_in_title.split(" "))) and ratio<0.8:
                    continue
            filtered.append(link)
        if limit == len(filtered): return filtered
    return filtered

def convert_date(date):
    try:
        return parser.parse(date, default=datetime.date(1979,1,1))
    except:
        return None

def get_domain(website):
    if website is None:
        return None
    website = website.lower().replace("https://","").replace("http://","").replace("www.","")
    domain = website.split("/")[0]
    return domain

def domain_match(website1,website2):
    return website1 and website2 and get_domain(website2) == get_domain(website1)

def name_match(name1, name2, intersect_threshold=2):
    name1 = re.sub('[^0-9a-z\s]','',name1.lower())
    name2 = re.sub('[^0-9a-z\s]','',name2.lower())
    if len(name1) < 3 or len(name2) < 3:
        return False
    name1_words = set(name1.split(" "))
    name2_words = set(name2.split(" "))
    stop_words = ["the", "of","and","a","the","at","for","in","on"]
    for stop_word in stop_words:
        if stop_word in name1_words: name1_words.remove(stop_word)
        if stop_word in name2_words: name2_words.remove(stop_word)
    intersect = name1_words & name2_words
    intersect_threshold = min(intersect_threshold, len(name2_words))
    intersect_threshold = min(intersect_threshold, len(name2_words))
    if len(intersect)>=intersect_threshold: return True
    ratio = SequenceMatcher(None, name1, name2)
    if ratio>=0.8: return True
    return False

def get_firstname(str):
    str = re.sub(" - "," ",str)
    str = re.sub("[^a-zA-Z-]"," ",str)
    str = re.sub("\s+"," ",str.lower().strip())
    firstname = str.split(" ")[0]
    if firstname in ["ms","mr","miss","mrs","dr", "rev", "reverend","professor","prof","md"] and len(str.split(" "))>1: firstname =  str.split(" ")[1]
    return firstname

def common_institutions(p1,p2, intersect_threshold=5):
    commonalities = set()
    common_schools = common_school_ids(p1,p2)
    commonalities.update(common_schools)
    common_companies = common_company_ids(p1,p2)
    commonalities.update(common_companies)
    common_school_names = match_common_school_names(p1,p2, intersect_threshold=intersect_threshold)
    commonalities.update(common_school_names)
    common_company_names = match_common_company_names(p1,p2, intersect_threshold=intersect_threshold)
    commonalities.update(common_company_names)
    commonalities = list(commonalities)
    return ", ".join(commonalities)

def parse_date(datestr):
    try:
        date = dateutil.parser.parse(datestr)
    except:
        date = None
    return date

def date_overlap(start_date1, end_date1, start_date2, end_date2):
    if (start_date1 <= start_date2 <= end_date1):
        return (start_date2, end_date1)
    if (start_date2 <= start_date1 <= end_date2):
        return (start_date1, end_date2)
    return None

def common_school_ids(p1, p2):
    matching = set()
    for school1 in p1.get("schools",[]):
        if not school1.get("college_id"): continue
        if not school1.get("start_date") and not school1.get("end_date"): continue
        start_date1 = parse_date(school1.get("start_date")).date() if parse_date(school1.get("start_date")) else datetime.date(1900,1,1)
        end_date1 = parse_date(school1.get("end_date")).date() if parse_date(school1.get("end_date")) else datetime.date.today()
        for school2 in p2.get("schools",[]):
            if not school2.get("college_id"): continue
            if not school2.get("start_date") and not school2.get("end_date"): continue
            start_date2 = parse_date(school2.get("start_date")).date() if parse_date(school2.get("start_date")) else datetime.date(1900,1,1)
            end_date2 = parse_date(school2.get("end_date")).date() if parse_date(school2.get("end_date")) else datetime.date.today()
            dates_overlap= date_overlap(start_date1, end_date1, start_date2, end_date2);
            if not dates_overlap: continue
            if school1.get("college_id") == school2.get("college_id"):
                matching.add("Attended " + school2.get("college") + " together " + str(dates_overlap[0].year) + "-" + str(dates_overlap[1].year))
    return matching

def common_company_ids(p1, p2):
    matching = set()
    for job1 in p1.get("experiences",[]):
        if not job1.get("company_id"): continue
        if not job1.get("start_date") and not job1.get("end_date"): continue
        start_date1 = parse_date(job1.get("start_date")).date() if parse_date(job1.get("start_date")) else datetime.date(1900,1,1)
        end_date1 = parse_date(job1.get("end_date")).date() if parse_date(job1.get("end_date")) else datetime.date.today()
        for job2 in p2.get("experiences",[]):
            if not job2.get("company_id"): continue
            if not job2.get("start_date") and not job2.get("end_date"): continue
            start_date2 = parse_date(job2.get("start_date")).date() if parse_date(job2.get("start_date")) else datetime.date(1900,1,1)
            end_date2 = parse_date(job2.get("end_date")).date() if parse_date(job2.get("end_date")) else datetime.date.today()
            dates_overlap= date_overlap(start_date1, end_date1, start_date2, end_date2);
            if not dates_overlap: continue
            if job1.get("company_id") == job2.get("company_id"):
                matching.add("Worked at " + job2.get("company") + " together " + str(dates_overlap[0].year) + "-" + str(dates_overlap[1].year))
    return matching

def match_common_company_names(p1, p2, intersect_threshold=3):
    matching = set()
    for job1 in p1.get("experiences",[]):
        if not job1.get("company"): continue
        if not job1.get("start_date") and not job1.get("end_date"): continue
        start_date1 = parse_date(job1.get("start_date")).date() if parse_date(job1.get("start_date")) else datetime.date(1900,1,1)
        end_date1 = parse_date(job1.get("end_date")).date() if parse_date(job1.get("end_date")) else datetime.date.today()
        for job2 in p2.get("experiences",[]):
            if not job2.get("company"): continue
            if not job2.get("start_date") and not job2.get("end_date"): continue
            if job1.get("company_id") and job2.get("company_id"): continue
            start_date2 = parse_date(job2.get("start_date")).date() if parse_date(job2.get("start_date")) else datetime.date(1900,1,1)
            end_date2 = parse_date(job2.get("end_date")).date() if parse_date(job2.get("end_date")) else datetime.date.today()
            dates_overlap= date_overlap(start_date1, end_date1, start_date2, end_date2);
            if not dates_overlap: continue
            if name_match(job2.get("company"), job1.get("company"), intersect_threshold=intersect_threshold):
                print uu(job2.get("company") + "-->" + job1.get("company"))
                if len(job2.get("company")) < len(job1.get("company")):
                    company_name = job2.get("company")
                else:
                    company_name = job1.get("company")
                matching.add("Worked at " + company_name + " together " + str(dates_overlap[0].year) + "-" + str(dates_overlap[1].year))
    return matching

def match_common_school_names(p1, p2, intersect_threshold=3):
    matching = set()
    for school1 in p1.get("schools",[]):
        if not school1.get("college"): continue
        if not school1.get("start_date") and not school1.get("end_date"): continue
        start_date1 = parse_date(school1.get("start_date")).date() if parse_date(school1.get("start_date")) else datetime.date(1900,1,1)
        end_date1 = parse_date(school1.get("end_date")).date() if parse_date(school1.get("end_date")) else datetime.date.today()
        for school2 in p2.get("schools",[]):
            if not school2.get("college"): continue
            if not school2.get("start_date") and not school2.get("end_date"): continue
            if school1.get("college_id") and school2.get("college_id"): continue
            start_date2 = parse_date(school2.get("start_date")).date() if parse_date(school2.get("start_date")) else datetime.date(1900,1,1)
            end_date2 = parse_date(school2.get("end_date")).date() if parse_date(school2.get("end_date")) else datetime.date.today()
            dates_overlap= date_overlap(start_date1, end_date1, start_date2, end_date2);
            if not dates_overlap: continue
            if name_match(school2.get("college"), school1.get("college"), intersect_threshold=intersect_threshold):
                print uu(school2.get("college") + "-->" + school1.get("college"))
                if len(school2.get("college")) < len(school1.get("college")):
                    school_name = school2.get("college")
                else:
                    school_name = school1.get("college")
                matching.add("Attended " + school_name + " together " + str(dates_overlap[0].year) + "-" + str(dates_overlap[1].year))
    return matching
