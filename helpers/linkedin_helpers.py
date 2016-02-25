import logging
import sys
import datetime
from helpers.stringhelpers import uu, name_match, random_string, csv_line_to_list
from helpers.data_helpers import merge_by_key
from helpers.datehelpers import parse_date, date_overlap

reload(sys) 
sys.setdefaultencoding('utf-8')

logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def collapse_commonalies(commonalities):
    collapsed = []
    for connection, date_ranges in commonalities.iteritems():
        start_date = min([date_range[0] for date_range in date_ranges])
        end_date = max([date_range[1] for date_range in date_ranges])
        start_date_str = str(start_date.year)
        end_date_str = 'Present' if end_date == datetime.date.today() else str(end_date.year)
        if connection and start_date_str and end_date_str:
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
            if not job2.get("company_id") or not job2.get("company"): continue
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
            if not school2.get("college_id") or not school2.get("college"): continue
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

def get_dob_year_range(educations, experiences):
    dob_year_min = None
    dob_year_max = None    
    school_milestones = get_school_milestones(educations)
    first_school_year = school_milestones.get("first_school_year")
    first_grad_year = school_milestones.get("first_grad_year")
    if first_school_year:
        dob_year_max = first_school_year - 17
        dob_year_min = first_school_year - 20
    elif first_grad_year:
        dob_year_max = first_grad_year - 21
        dob_year_min = first_grad_year - 25
    if dob_year_min: 
        dob_year_range = (dob_year_min, dob_year_max)
        return dob_year_range
    work_milestones = get_work_milestones(experiences)
    first_year_experience = work_milestones.get("first_year_experience")
    first_quitting_year = work_milestones.get("first_quitting_year")
    if first_year_experience:
        dob_year_max = first_year_experience - 18
        dob_year_min = first_year_experience - 24
    elif first_quitting_year:
        dob_year_max = first_quitting_year - 19
        dob_year_min = first_quitting_year - 28
    #add age-based fuzz factor for people who only list job years
    if dob_year_min:
        dob_year_min -= (datetime.datetime.today().year - dob_year_min)/10
        dob_year_range = (dob_year_min, dob_year_max)
        return dob_year_range
    first_weird_school_year = school_milestones.get("first_weird_school_year")
    first_weird_grad_year = school_milestones.get("first_weird_grad_year")
    if first_weird_school_year:
        dob_year_max = first_weird_school_year - 14
        dob_year_min = first_weird_school_year - 22
    elif first_weird_grad_year:
        dob_year_max = first_weird_grad_year - 17
        dob_year_min = first_weird_grad_year - 27
    dob_year_range = (dob_year_min, dob_year_max)
    return dob_year_range

def get_school_milestones(schools):
    first_school_year = None
    first_grad_year = None
    first_weird_school_year = None
    first_weird_grad_year = None
    if not schools:
        return {}
    for school in schools:
        start_date = parse_date(school.get("start_date"))
        end_date = parse_date(school.get("end_date"))
        college = school.get("college") if school.get("college") else ""
        if school.get("college_id") or college.lower().find('university')>-1 or college.lower().find('college')>-1:
            if start_date and (not first_school_year or start_date.year<first_school_year):
                first_school_year = start_date.year
            if end_date and (not first_grad_year or end_date.year<first_grad_year):
                    first_grad_year = end_date.year
        else:
            if start_date and (not first_weird_school_year or start_date.year<first_weird_school_year):
                first_weird_school_year = start_date.year
            if end_date and (not first_weird_grad_year or end_date.year<first_weird_grad_year):
                first_weird_grad_year = end_date.year
    return {"first_school_year":first_school_year,
            "first_grad_year": first_grad_year,
            "first_weird_school_year":first_weird_school_year,
            "first_weird_grad_year": first_weird_grad_year}

def get_work_milestones(jobs):
    if not jobs:
        return {}
    first_year_experience = None
    first_quitting_year = None
    for job in jobs:
        start_date = parse_date(job.get("start_date"))
        end_date = parse_date(job.get("end_date"))        
        if start_date and (not first_year_experience or start_date.year<first_year_experience):
            first_year_experience = start_date.year
        if end_date and (not first_quitting_year or end_date.year<first_quitting_year):
            first_quitting_year = end_date.year
    return {"first_year_experience":first_year_experience, "first_quitting_year":first_quitting_year}

def process_csv(csv):
    if not csv:
        return None
    lines = csv.splitlines()
    if len(lines)<2:
        return None
    header = lines[0]
    cols = csv_line_to_list(header)
    try:
        first_name_index = cols.index('First Name')
        last_name_index = cols.index('Last Name')
        company_index = cols.index('Company')
        job_title_index = cols.index('Job Title')
        email_index = cols.index('E-mail Address')
    except Exception, e:
        try:
            #yahoo format
            first_name_index = cols.index('First')
            last_name_index = cols.index('Last')
            company_index = cols.index('Company')
            job_title_index = cols.index('Title')
            email_index = cols.index('Email')     
        except:
            return None
    if min(first_name_index, last_name_index, company_index, job_title_index, email_index) < 0:
        return None
    data = []
    print "Processing CSV"
    for i in xrange(1, len(lines)):
        line = csv_line_to_list(lines[i])
        if len(line) <= max(first_name_index, last_name_index, company_index, job_title_index, email_index):
            print "Linkedin csv line is wrong:\r\n{}".format(lines[i])
            continue
        print line
        contact = {}
        contact["first_name"] = line[first_name_index].decode('latin-1')
        contact["last_name"] = line[last_name_index].decode('latin-1')
        contact["companies"] = [line[company_index].decode('latin-1')]
        contact["email"] = [{"address": line[email_index].decode('latin-1')}]
        contact["job_title"] = line[job_title_index].decode('latin-1')
        data.append({"contact":contact, "contacts_owner":None, "service":"LinkedIn"})
    return data    
