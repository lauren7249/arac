from constants import profile_re, bloomberg_company_re, school_re, company_re, SOCIAL_DOMAINS
import itertools
import operator
import re
import datetime
import dateutil
import json
import logging
from difflib import SequenceMatcher
from random import shuffle
import numpy as np
import collections

logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def uu(str):
    if str:
        try:
            return str.decode("ascii", "ignore").encode("utf-8")
        except:
            return str.encode('UTF-8')
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

def get_domain(website):
    if website is None:
        return None
    website = website.lower().replace("https://","").replace("http://","").replace("www.","")
    domain = website.split("/")[0]
    return domain

def domain_match(website1,website2):
    return website1 and website2 and get_domain(website2) == get_domain(website1)

def name_match(name1, name2, intersect_threshold=5):
    name1 = re.sub('[^0-9a-z\s]','',name1.lower())
    name2 = re.sub('[^0-9a-z\s]','',name2.lower())
    if name1 and name2 and name1 == name2:
        return True
    if len(name1) < 3 or len(name2) < 3:
        return False
    name1_words = set(name1.split(" "))
    name2_words = set(name2.split(" "))
    stop_words = ["the", "of","and","a","the","at","for","in","on","school","","inc","llc","co"]
    for stop_word in stop_words:
        if stop_word in name1_words: name1_words.remove(stop_word)
        if stop_word in name2_words: name2_words.remove(stop_word)
    intersect = name1_words & name2_words
    intersect_threshold = min(intersect_threshold, len(name1_words))
    intersect_threshold = min(intersect_threshold, len(name2_words))
    if len(intersect)>=intersect_threshold: 
        logger.info("Name match: %s == %s", name1, name2)
        return True
    ratio = SequenceMatcher(None, name1, name2)
    if ratio>=0.8: 
        logger.info("Name match: %s == %s", name1, name2)
        return True
    return False

def get_firstname(str):
    if not str:
        return str
    str = re.sub(" - "," ",str)
    str = re.sub("[^a-zA-Z-]"," ",str)
    str = re.sub("\s+"," ",str.lower().strip())
    firstname = str.split(" ")[0]
    if firstname in ["ms","mr","miss","mrs","dr", "rev", "reverend","professor","prof","md"] and len(str.split(" "))>1: firstname =  str.split(" ")[1]
    return firstname

def merge_by_key(d1, d2):
    merged = {}
    for key in set(d1.keys()) & set(d2.keys()):
        merged[key] = d1[key] + d2[key]
    for key in set(d1.keys()) - set(d2.keys()):
        merged[key] = d1[key]     
    for key in set(d2.keys()) - set(d1.keys()):
        merged[key] = d2[key]              
    return merged

def common_institutions(p1,p2, intersect_threshold=5):
    commonalities = {}
    common_schools = common_school_ids(p1,p2)
    commonalities = merge_by_key(common_schools, commonalities)
    common_companies = common_company_ids(p1,p2)
    commonalities = merge_by_key(common_companies, commonalities)
    common_school_names = match_common_school_names(p1,p2, intersect_threshold=intersect_threshold)
    commonalities = merge_by_key(common_school_names, commonalities)
    common_company_names = match_common_company_names(p1,p2, intersect_threshold=intersect_threshold)
    commonalities = merge_by_key(common_company_names, commonalities)
    commonalities = collapse_commonalies(commonalities)
    return ", ".join(commonalities)

DEFAULT_DATE = dateutil.parser.parse('January 1')
def parse_date(datestr):
    try:
        date = dateutil.parser.parse(datestr, default=DEFAULT_DATE)
    except:
        date = None
    return date

def date_overlap(start_date1, end_date1, start_date2, end_date2):
    if (start_date1 <= start_date2 <= end_date1):
        return (start_date2, end_date1)
    if (start_date2 <= start_date1 <= end_date2):
        return (start_date1, end_date2)
    return None

def collapse_commonalies(commonalities):
    collapsed = []
    for connection, date_ranges in commonalities.iteritems():
        start_date = min([date_range[0] for date_range in date_ranges])
        end_date = max([date_range[1] for date_range in date_ranges])
        start_date_str = str(start_date.year)
        end_date_str = 'Present' if end_date == datetime.date.today() else str(end_date.year)
        collapsed.append(connection + start_date_str + "-" + end_date_str)
    return collapsed

def common_company_ids(p1, p2):
    matching = {}
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
                connection = "Worked at " + job2.get("company") + " together "
                matching[connection] = matching.get(connection,[]) + [dates_overlap]
    return matching

def match_common_company_names(p1, p2, intersect_threshold=3):
    matching = {}
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
                connection = "Worked at " + company_name + " together "
                matching[connection] = matching.get(connection,[]) + [dates_overlap]
    return matching

def common_school_ids(p1, p2):
    matching = {}
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
                connection = "Attended " + school2.get("college") + " together "
                matching[connection] = matching.get(connection,[]) + [dates_overlap]
    return matching

def match_common_school_names(p1, p2, intersect_threshold=3):
    matching = {}
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
                connection = "Attended " + school_name + " together "
                matching[connection] = matching.get(connection,[]) + [dates_overlap]
    return matching

def get_specific_url(social_accounts, type="linkedin.com"):
    for account in social_accounts:
        if account.find(type) > -1: return account
    return None

def sort_social_accounts(social_accounts):
    d = {}
    for link in social_accounts: 
        domain = link.replace("https://","").replace("http://","").split("/")[0].replace("www.","").split(".")[0].lower()
        if domain in SOCIAL_DOMAINS: 
            d[domain] = link  
    return d  

def flatten(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        if not v and v != 0:
            continue
        if isinstance(v, list):
            continue
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)