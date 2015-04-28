
def clean(str):
    try:
        str = re.sub(" - "," ",str)
        str = re.sub("[^a-zA-Z-0-9]"," ",str)
        str = re.sub("\s+"," ",str.lower().strip())
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
import csv

def main():
    companies = pandas.read_csv('https://s3.amazonaws.com/advisorconnect-bigfiles/raw/companies.txt', usecols=['name'], sep="\t")
    companies.name = companies.name.apply(clean)
    companies.drop_duplicates(inplace=True, subset=["name"])

    numbers_path = "numbers.csv"
    if os.path.isfile(numbers_path): os.remove(numbers_path)

    pool = multiprocessing.Pool(100)
    for index, row in companies.iterrows():
        pool.apply_async(get_number,(row.name,))

    companies=None
    pool.close()
    pool.join()