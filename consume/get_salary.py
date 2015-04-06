import os 
import pandas
import requests
import lxml.html
import multiprocessing
import re
from datetime import date

salaries_path = "salaries.csv"

def clean(str):
    try:
        str = re.sub("\s+"," ",str.lower())
        str = re.sub("\n"," ", str)
    except:
        pass
    return str

def parse_out(text, startTag, endTag):
    region = ""
    region_start = text.find(startTag)
    if region_start > -1:
        region = text[region_start+len(startTag):]
        region_end = region.find(endTag)
        if region_end > -1:
            region = region[:region_end]    
    return region

def calculate_salary(title):
    headers ={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    url =  "http://www.indeed.com/salary?q1=%s" % (title)       
    try:
        response = requests.get(url, headers=headers)
        response_text = response.content
        salary_raw = parse_out(response_text,'<span class="salary">', '<img src=')
        salary = float(re.sub("\$","",re.sub(",","", salary_raw)))
        with open(salaries_path,"ab") as f:
            f.write('"' + title + '",' + str(salary) + "\n")
            f.close()
    except Exception, err:
        pass

def getYear(date):
    try:
        return date.year
    except:
        pass
    return None

titles = pandas.read_csv('https://s3.amazonaws.com/advisorconnect-bigfiles/raw/jobs.txt', usecols=["title","prospect_id","end_date"], sep="\t", parse_dates=["end_date"])
titles.fillna("", inplace=True)
titles.end_date = titles.end_date.apply(getYear)
today = date.today().year
titles.end_date.fillna(today, inplace=True)
titles = titles.groupby('prospect_id', group_keys=False).apply(lambda x: x.ix[x.end_date.idxmax()])
titles.title = titles.title.apply(clean)

titles.to_csv(path_or_buf="current_prospect_jobs.csv", index=False, columns=["prospect_id","title"])
titles.drop_duplicates(inplace=True, subset=["title"])
raw_titles = list(titles["title"].values)

print len(raw_titles)
if os.path.isfile(salaries_path): os.remove(salaries_path)

pool = multiprocessing.Pool(100)
pool.map(calculate_salary,raw_titles)