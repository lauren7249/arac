

salaries_path = "salaries.csv"

def clean(str):
    try:
        str = re.sub(" - "," ",str)
        str = re.sub("[^a-zA-Z-]"," ",str)
        str = re.sub("\s+"," ",str.lower().strip())
        # wordlist = str.split(" ")
        # wordlist.sort()
        # str = " ".join(wordlist)
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

import os 
import pandas
import requests
import lxml.html
import multiprocessing
from multiprocessing import Manager
import re
from datetime import date
from joblib import Parallel, delayed
import csv

global latestJobs
latestJobs = {}


def getYear(date):
    try:
        return int(date.split("-")[0])
    except:
        pass
    return None

def getMaxYear(row):
    return row.ix[row["end_date"].idxmax()]


def updateLatestJob(job):
    latestJob = latestJobs.get(job[0])
    if latestJob is None or latestJob[2] < job[2]:
        latestJobs.update({job[0]:job})

today = date.today()
titles = pandas.read_csv('https://s3.amazonaws.com/advisorconnect-bigfiles/raw/jobs.txt', usecols=["title","prospect_id","end_date"], sep="\t")
titles.end_date.fillna(str(today),inplace=True)
titles.end_date = titles.end_date.apply(getYear)
titles.title = titles.title.apply(clean)
titles.to_csv(path_or_buf="prospect_jobs.csv", index=False, header=None, columns=["prospect_id","title","end_date"])
titles = None

t = open("prospect_jobs.csv",'rb')
reader = csv.reader(t, delimiter=',')
for row in reader:
    updateLatestJob(row)
t.close()
   
if os.path.isfile("current_prospect_jobs.csv"): os.remove("current_prospect_jobs.csv")
t = open("current_prospect_jobs.csv","ab")
writer = csv.writer(t)
for key, value in latestJobs.iteritems():
    writer.writerow(value)
t.close()
latestJobs = None

titles = pandas.read_csv("current_prospect_jobs.csv", sep=",", names=["prospect_id","title","end_date"], header=None, usecols=["title"])
titles.drop_duplicates(inplace=True, subset=["title"])

if os.path.isfile(salaries_path): os.remove(salaries_path)

pool = multiprocessing.Pool(100)
for index, row in titles.iterrows():
    pool.apply_async(calculate_salary,(row.title,))

titles = None
pool.close()
pool.join()