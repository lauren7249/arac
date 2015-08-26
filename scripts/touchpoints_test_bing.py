import pandas
import us
import datetime
from prime.utils import bing, r
from prime.prospects.get_prospect import *

tp = pandas.read_csv("~/advisorCONNECT 6-10-15 Test Input.csv")
tp["zip"] = tp["Zip Code"].apply(lambda z: int(z.split("-")[0]))
#3500
tp.drop_duplicates(subset=["First Name","Last Name", "Age", "zip"], inplace=True)
#2215
zips = pandas.read_csv("~/zipcode.csv")
zips.rename(columns={"latitude":"tp_lat","longitude":"tp_lng"}, inplace=True)
zips = zips[["zip","tp_lat","tp_lng"]]

tp =tp.merge(zips, how="inner", on=["zip"])
#2161


def get_name(row):
    if str(row["Middle Name"]) == "nan": 
        name = row["First Name"] + " " + row["Last Name"]
    else: 
        name = row["First Name"] + " " + row["Middle Name"] + " " + row["Last Name"]
    return name


for index, row in tp.iterrows():
    name = get_name(row)
    terms = name  + " " + us.states.lookup(row["State"]).name   
    urls = bing.search_linkedin_profile(terms, name, limit=10)
    for url in urls:
        r.sadd("urls",url)

matches = {}
for index, row in tp.iterrows():
    name = get_name(row)
    terms = name  + " " + us.states.lookup(row["State"]).name      
    urls = bing.search_linkedin_profile(terms, name, limit=10)
    id = row["ID Number"]
    age_matches = []
    for url in urls:
        p = from_url(url)
        if p and (datetime.datetime.now().date() - p.updated).days > 120:
            r.sadd("urls",url)
        else:
            if p.age and row.Age and abs(p.age - row.Age) <=5: 
                print url
                age_matches.append(url)    
    if age_matches: matches.update({id:set(age_matches)})

age_matches_ages = []
for index, row in tp.iterrows():
    id = row["ID Number"]
    if matches.get(id): age_matches_ages.append(row.Age)
    else: print get_name(row) + " Age: " + str(row.Age) + " Zip: " + str(row.zip)
#44.5
print numpy.median(age_matches_ages)
#55.5
print numpy.median(tp.Age)
