from difflib import SequenceMatcher
from consume.li_scrape_job import query_prospects
import re, pandas
from prime.utils import profile_re

#according to linkedin (https://www.linkedin.com/edu/alumni?id=36114) there are 237
school_name = "Thomas More College of Liberal Arts"

#https://api.datamarket.azure.com/Bing/SearchWeb/v1/Web?Query=%27site%3Alinkedin.com%20inbody%3A%22Thomas%20More%20College%20of%20Liberal%20Arts%22%27
df = pandas.read_csv("/Users/lauren/Documents/data/Thomas More College of Liberal Arts.csv")

profiles = set()
for index, row in df.iterrows():
    url = row.Url
    if re.search(profile_re,url): profiles.add(url)

recs = query_prospects(profiles)
hits=0
for prospect in recs:
    for school in prospect.schools:
        if school.name == school_name: hits+=1
        else: 
            ratio = SequenceMatcher(None, school_name.lower(), school.name.lower().strip()).ratio()
            if ratio>0.8: 
                hits+=1
                print school.name

#222 hits