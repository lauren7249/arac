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
school = "Syracuse"
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
            coords.append(None)
            continue
        dob_years.append(p.dob_year_range)
        mapquest_coords = geocode.get_mapquest_coordinates(p.location_raw)
        coords.append(mapquest_coords)
    return (dob_years, coords)

pool = multiprocessing.Pool(10)

r.delete("job_urls")
urls = pool.map(process, tp[[firstname,lastname]].to_records())

#5348 bing requests
#2002 urls
#seconds_scraped, urls_scraped = scrape_job(r.smembers("job_urls"))


r.delete("job_urls_nicknames")
nickname_urls = pool.map(process_nicknames, tp[[firstname,lastname]].to_records())

#seconds_scraped, urls_scraped = scrape_job(r.smembers("job_urls_nicknames"))

dob_years_coords = pool.map(get_info_for_urls, urls)
dob_years_coords_nicknames = pool.map(get_info_for_urls, nickname_urls)

def find_matches(current_urls, dob_years, coords, tp_dob_year, tp_lat, tp_lng):
    match_urls = []
    for i in xrange(0,len(current_urls)):
        newrow = row
        url = current_urls[i]
        dob_year = dob_years[i]
        mapquest_coords = coords[i]
        if not mapquest_coords: continue
        age_matches = (dob_year and tp_dob_year and abs(dob_year - tp_dob_year) <=8) or not dob_year or not tp_dob_year
        if not age_matches: continue
        latlng = mapquest_coords.get("latlng")
        if not latlng: continue
        point1 = GeoPoint(latlng[0],latlng[1])
        point2 = GeoPoint(tp_lat, tp_lng)
        miles_apart = point2.distance_to(point1)         
        location_matches = miles_apart is not None and miles_apart < 75
        if not location_matches: continue
        match_urls.append(url)
    return match_urls

matches = []
total_matches = 0
perfect_matches = 0
for index, row in tp.iterrows():
    if len(row.TouchPointsDateOfBirth.strip()): tp_dob_year = int(row.TouchPointsDateOfBirth.split('/')[-1])
    elif len(row.CLASS_YEAR.strip()): tp_dob_year = int(row.CLASS_YEAR) - 22
    else: tp_dob_year = None
    current_urls = urls[index]
    dob_years, coords = dob_years_coords[index]
    real_match_urls = find_matches(current_urls, dob_years, coords, tp_dob_year, row.tp_lat, row.tp_lng)
    if len(real_match_urls): 
        matches.append(real_match_urls)
        total_matches+=1
        perfect_matches+=1
        continue
    if len(current_urls):
        print row[firstname] + " " + row[lastname] + " " + row.TouchPointsDateOfBirth + " " + row.CLASS_YEAR + " " + row.TouchPointsAddress1City + " " + row.TouchPointsAddress1State
        print current_urls
    current_urls = nickname_urls[index]
    dob_years, coords = dob_years_coords_nicknames[index]
    nickname_match_urls = find_matches(current_urls, dob_years, coords, tp_dob_year, row.tp_lat, row.tp_lng)
    if len(nickname_match_urls): 
        matches.append(nickname_match_urls)
        total_matches+=1
        continue
    matches.append(None)

       
