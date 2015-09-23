import pandas
import us
import datetime
from prime.utils import bing, r, get_bucket, geocode
from prime.prospects.get_prospect import *
from geoindex.geo_point import GeoPoint
from boto.s3.key import Key
from consume.convert import parse_html, uu
import multiprocessing
from consume.li_scrape_job import *

#2884
tp = pandas.read_csv("/Users/lauren/Documents/data/touchpoints/advisorCONNECT 9-17-15 Test Input.csv")

firstname = "TouchPointsFirstName"
lastname = "TouchPointsLastName"
dob = "TouchPointsDateOfBirth"
zipcode = "TouchPointsAddress1Zip"
school = "Davis"

tp_columns = list(tp.columns.values)
tp["zip"] = tp[zipcode].apply(lambda z: int(z.split("-")[0]))
#2882
tp.drop_duplicates(subset=[firstname,lastname, dob, "zip"], inplace=True)

zips = pandas.read_csv("~/zipcode.csv")
zips.rename(columns={"latitude":"tp_lat","longitude":"tp_lng"}, inplace=True)
zips = zips[["zip","tp_lat","tp_lng"]]

#2836
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
    urls = bing.search_linkedin_by_name(name, school=school, page_limit=30, limit=300)
    if len(urls) == 0: urls = bing.search_linkedin_by_name(name, page_limit=30, limit=300)
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
        #  if re.sub('[^A-Za-z]','',school).lower() == re.sub('[^A-Za-z]','',s.name).lower(): 
        #   school_matches = True
        #   break
        # if not school_matches: 
        #  dob_years.append(None)
        #  coords.append([])
        #  continue       
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
#3156 bing hits
#22 max bing hits per person
urls = pool.map(process, tp[[firstname,lastname]].to_records())

#2295
has_urls =0
for rec in urls:
    if len(rec)>0: has_urls+=1

#876 seconds for 4688
seconds_scraped, urls_scraped = scrape_job(r.smembers("job_urls"))



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
        if not location_matches: continue
        match_urls.append(url)
    return match_urls

matches = []
total_matches = 0
perfect_matches = 0
output_df = pandas.DataFrame()
for index, row in tp.iterrows():
    if len(row[dob].strip()): tp_dob_year = int(row[dob].split('/')[-1])
    elif 'CLASS_YEAR' in tp_columns and len(row.CLASS_YEAR.strip()): tp_dob_year = int(row.CLASS_YEAR) - 22
    else: tp_dob_year = None
    current_urls = urls[index]
    dob_years, coords = dob_years_coords[index]
    tp_point = GeoPoint(row.tp_lat, row.tp_lng) if row.tp_lat and row.tp_lng else None
    # if len(current_urls) == 0 and tp_dob_year > 1970:
    #     print row[firstname] + " " + row[lastname] + " " + row[dob] + " " + row.TouchPointsAddress1City + " " + row.TouchPointsAddress1State  
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
                if re.search(re.sub('[^a-z]','',school.lower()),re.sub('[^a-z]','',s.name.lower())): 
                    school_match = s
                    break 
            if school_match or (not p.schools and (max(p.dob_year_range) or p.location_raw)) or (max(p.dob_year_range) and p.location_raw):
                newrow = row
                if not school_match and p.schools: school_match = p.schools[-1]
                newrow['TouchPoints Job Title'] = uu(p.current_job.title.replace('\n',' ')) if p.current_job else ''
                newrow['TouchPoints Employer'] = uu(p.current_job.company.name.replace('\n',' ')) if p.current_job and p.current_job.company else ''
                newrow['TouchPoints Employer Start'] = p.current_job.start_date if p.current_job else ''
                newrow['TouchPoints Employer End'] = p.current_job.end_date if p.current_job else ''
                if school_match:
                    newrow['TouchPoints School'] = uu(school_match.school.name.replace('\n',' ')) if school_match.school else ''
                    newrow['TouchPoints Degree and Major'] = uu(school_match.degree.replace('\n',' ')) if school_match.degree else ''
                    newrow['TouchPoints School Start'] = school_match.start_date.year if school_match.start_date else ''
                    newrow['TouchPoints School End'] = school_match.end_date.year if school_match.end_date else ''
                newrow['first_name'] = " ".join(p.name.split()[:-1])
                newrow['last_name'] = p.name.split()[-1]
                newrow['TouchPoints Industry'] = uu(p.industry_raw)
                newrow['TouchPoints Interests'] = uu(", ".join(p.json.get("interests",[])).replace('\n',' '))
                newrow['TouchPoints Causes'] = uu(", ".join(p.json.get("causes",[])).replace('\n',' '))
                newrow['TouchPoints Organizations'] = uu(", ".join(p.json.get("organizations",[])).replace('\n',' '))
                output_df = output_df.append(newrow, ignore_index=True)
                break
            else:
                print row[firstname] + " " + row[lastname] + " " + row[dob] + " " + row.TouchPointsAddress1City + " " + row.TouchPointsAddress1State  + " " + url
  # if len(current_urls):
  #  print row[firstname] + " " + row[lastname] + " " + row.TouchPointsDateOfBirth + " " + row.CLASS_YEAR + " " + row.TouchPointsAddress1City + " " + row.TouchPointsAddress1State
  #  print current_urls
  # current_urls = nickname_urls[index]
  # dob_years, coords = dob_years_coords_nicknames[index]
  # nickname_match_urls = find_matches(current_urls, dob_years, coords, tp_dob_year, row.tp_lat, row.tp_lng)
  # if len(nickname_match_urls): 
  #  matches.append(nickname_match_urls)
  #  total_matches+=1
  #  continue
  # matches.append(None)
new_columns = ["TouchPoints Employer", "TouchPoints Job Title", "TouchPoints Industry", "TouchPoints Employer Start", "TouchPoints Employer End", "TouchPoints School", "TouchPoints Degree and Major", "TouchPoints School Start", "TouchPoints School End", "TouchPoints Interests", "TouchPoints Causes", "TouchPoints Organizations", "first_name","last_name"]
output_df = output_df[tp_columns + new_columns]
output_df.fillna('',inplace=True)
output_df.to_csv('/Users/lauren/Documents/data/touchpoints/17Sep2015.touchpoints.matches.csv', encoding='utf-8', index=None)
