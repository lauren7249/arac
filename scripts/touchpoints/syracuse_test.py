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
        dob_years.append(p.dob_year)
        mapquest_coords = geocode.get_mapquest_coordinates(p.location_raw)
        coords.append(mapquest_coords)
    return (dob_years, coords)

pool = multiprocessing.Pool(10)

r.delete("job_urls")
urls = pool.map(process, tp[[firstname,lastname]].to_records())

#5348 bing requests
#2002 urls
seconds_scraped, urls_scraped = scrape_job(r.smembers("job_urls"))


r.delete("job_urls_nicknames")
nickname_urls = pool.map(process_nicknames, tp[[firstname,lastname]].to_records())

seconds_scraped, urls_scraped = scrape_job(r.smembers("job_urls_nicknames"))

dob_years_coords = pool.map(get_info_for_urls, urls)
dob_years_coords_nicknames = pool.map(get_info_for_urls, nickname_urls)
for index, row in tp.iterrows():
    current_urls = urls[index]
    dob_years, coords = dob_years_coords[index]
    for i in xrange(0,len(current_urls)):
        url = current_urls[i]
        dob_year = dob_years[i]
        mapquest_coords = coords[i]
        break

