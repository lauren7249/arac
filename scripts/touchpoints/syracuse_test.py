import pandas
import us
import datetime
from prime.utils import bing, r, get_bucket, geocode
from prime.prospects.get_prospect import *
from geoindex.geo_point import GeoPoint
from boto.s3.key import Key
from consume.consumer import parse_html
import multiprocessing
from consume.li_scrape_job import *

firstname = "TouchPointsFirstName"
lastname = "TouchPointsLastName"
dob = "TouchPointsDateOfBirth"
zipcode = "TouchPointsAddress1Zip"
school = "Syracuse University"
bucket = get_bucket(bucket_name='chrome-ext-uploads')

#5416
tp = pandas.read_csv("/Users/lauren/Documents/data/touchpoints/advisorCONNECT 9-5-15 Test Input.csv")
tp_columns = list(tp.columns.values)
tp["zip"] = tp[zipcode].apply(lambda z: int(z.split("-")[0]))
#5416
tp.drop_duplicates(subset=[firstname,lastname, dob, "zip"], inplace=True)

zips = pandas.read_csv("~/zipcode.csv")
zips.rename(columns={"latitude":"tp_lat","longitude":"tp_lng"}, inplace=True)
zips = zips[["zip","tp_lat","tp_lng"]]

#5358
tp =tp.merge(zips, how="inner", on=["zip"])
tp.fillna('',inplace=True)
nicknames = pandas.read_csv("/Users/lauren/Documents/data/touchpoints/Nickname Database.csv", index_col="Name")
nicknames.fillna('', inplace=True)
nicknames_dict = {}
for index, row in nicknames.iterrows():
    nnames = set(row.values)
    if '' in nnames: nnames.remove('')
    nicknames_dict[index] = nnames


def process(row):
    name = row[1] + " " + row[2]
    urls = bing.search_linkedin_by_name(name, school=school, page_limit=10, limit=300)
    for url in urls:
        r.sadd("job_urls",url)
    return urls

def process_nicknames(row):
    fname = row[1] 
    nnames = nicknames_dict.get(fname.lower().strip(),[])
    urls = []
    for nickname in nnames:
        name = nickname + " " + row[2]
        nurls = bing.search_linkedin_by_name(name, school=school, page_limit=10, limit=300)
        for url in nurls:
            r.sadd("job_urls_nicknames",url)
            urls.append(url)
    return urls

def get_info_for_urls(urls):
    dob_years = []
    coords = []
    for url in urls:
        p = from_url(url)
        if not p: 
            dob_years.append(None)
            coords.append([])
            continue
        # school_matches = False        
        # for s in p.schools:
        #     if re.sub('[^A-Za-z]','',school).lower() == re.sub('[^A-Za-z]','',s.name).lower(): 
        #         school_matches = True
        #         break
        # if not school_matches: 
        #     dob_years.append(None)
        #     coords.append([])
        #     continue                      
        dob_years.append(p.dob_year_range)
        locations = []
        mapquest_coords = geocode.get_mapquest_coordinates(p.location_raw)
        if mapquest_coords and mapquest_coords.get("latlng"): locations.append(mapquest_coords.get("latlng"))
        for job in p.jobs:
            if not job.location: continue
            mapquest_coords = geocode.get_mapquest_coordinates(job.location)
            if mapquest_coords and mapquest_coords.get("latlng") and mapquest_coords.get("latlng") not in locations: locations.append(mapquest_coords.get("latlng"))                
        coords.append(locations)
    return (dob_years, coords)

pool = multiprocessing.Pool(7)

r.delete("job_urls")
urls = pool.map(process, tp[[firstname,lastname]].to_records())

#5338 bing requests
#1128 urls
#seconds_scraped, urls_scraped = scrape_job(r.smembers("job_urls"))


#r.delete("job_urls_nicknames")
#nickname_urls = pool.map(process_nicknames, tp[[firstname,lastname]].to_records())

#seconds_scraped, urls_scraped = scrape_job(r.smembers("job_urls_nicknames"))

dob_years_coords = pool.map(get_info_for_urls, urls)
#dob_years_coords_nicknames = pool.map(get_info_for_urls, nickname_urls)

def find_matches(current_urls, dob_years, coords, tp_dob_year, tp_point):
    match_urls = []
    for i in xrange(0,len(current_urls)):
        newrow = row
        url = current_urls[i]
        dob_year_range = dob_years[i]
        locations = coords[i]
       # age_matches = 
        age_matches =not dob_year_range or  not max(dob_year_range) or not tp_dob_year or (dob_year_range and max(dob_year_range) and tp_dob_year and tp_dob_year>=min(dob_year_range) and tp_dob_year<=max(dob_year_range)) 
        if not age_matches: continue
        location_matches = False
        for latlng in locations:
            point = GeoPoint(latlng[0],latlng[1])
            miles_apart = tp_point.distance_to(point)         
            location_matches = miles_apart is not None and miles_apart < 75
            if location_matches: break
        if not location_matches: 
            #if len(match_urls) == 0: print url
            continue
        match_urls.append(url)
    return match_urls

matches = []
total_matches = 0
perfect_matches = 0
output_df = pandas.DataFrame()
for index, row in tp.iterrows():
    if len(row.TouchPointsDateOfBirth.strip()): tp_dob_year = int(row.TouchPointsDateOfBirth.split('/')[-1])
    elif len(row.CLASS_YEAR.strip()): tp_dob_year = int(row.CLASS_YEAR) - 22
    else: tp_dob_year = None
    current_urls = urls[index]
    dob_years, coords = dob_years_coords[index]
    tp_point = GeoPoint(row.tp_lat, row.tp_lng) if row.tp_lat and row.tp_lng else None
    # if len(current_urls) == 0 and tp_dob_year > 1970 and len(row.CLASS_YEAR):
    #     print row[firstname] + " " + row[lastname] + " " + row.TouchPointsDateOfBirth + " " + row.CLASS_YEAR + " " + row.TouchPointsAddress1City + " " + row.TouchPointsAddress1State    
    if not tp_point or not len(dob_years): continue
    real_match_urls = find_matches(current_urls, dob_years, coords, tp_dob_year, tp_point)
    if len(real_match_urls): 
        matches.append(real_match_urls)
        total_matches+=1
        perfect_matches+=1
        for url in real_match_urls:
            p = from_url(url)
            school_match = None
            for s in p.schools:
                if re.match(re.sub('[^a-z]','',school.lower()),re.sub('[^a-z]','',s.name.lower())): 
                    school_match = s
                    break 
            if school_match:
                newrow = row
                newrow['current_job_title'] = p.current_job.title if p.current_job else ''
                newrow['current_job_company'] = p.current_job.company.name if p.current_job and p.current_job.company else ''
                newrow['current_job_start_date'] = p.current_job.start_date if p.current_job else ''
                newrow['current_job_end_date'] = p.current_job.end_date if p.current_job else ''
                newrow['current_job_location'] = p.current_job.location if p.current_job else ''
                newrow['school_name'] = school_match.school.name if school_match.school else ''
                newrow['school_degree_and_major'] = school_match.degree
                newrow['school_start_date'] = school_match.start_date
                newrow['school_end_date'] = school_match.end_date
                newrow['full_name'] = p.name
                newrow['industry'] = p.industry_raw
                newrow['location'] = p.location_raw
                newrow['interests'] = p.json.get("interests","")
                newrow['skills'] = p.json.get("skills","")
                newrow['causes'] = p.json.get("causes","")
                newrow['organizations'] = p.json.get("organizations","")
                output_df = output_df.append(newrow, ignore_index=True)
                break

    # if len(current_urls):
    #     print row[firstname] + " " + row[lastname] + " " + row.TouchPointsDateOfBirth + " " + row.CLASS_YEAR + " " + row.TouchPointsAddress1City + " " + row.TouchPointsAddress1State
    #     print current_urls
    # current_urls = nickname_urls[index]
    # dob_years, coords = dob_years_coords_nicknames[index]
    # nickname_match_urls = find_matches(current_urls, dob_years, coords, tp_dob_year, row.tp_lat, row.tp_lng)
    # if len(nickname_match_urls): 
    #     matches.append(nickname_match_urls)
    #     total_matches+=1
    #     continue
    # matches.append(None)

output_df = output_df[tp_columns + ['full_name','industry', 'location', 'school_name', 'school_degree_and_major', 'school_start_date', 'school_end_date','current_job_title','current_job_company','current_job_start_date','current_job_end_date', 'current_job_location', 'interests', "skills",'causes', 'organizations']]
output_df.fillna('',inplace=True)
output_df.to_csv('/Users/lauren/Documents/data/14Sep2015.touchpoints.matches.csv', encoding='utf-8', index=None)
