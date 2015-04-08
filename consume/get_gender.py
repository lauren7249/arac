import os 
import pandas
import multiprocessing
import re
from datetime import date
import csv
import requests
import json, urllib2
from gender_detector import GenderDetector 
from genderizer.genderizer import Genderizer
import sexmachine.detector as gender

global detector1
global detector2
detector1 = GenderDetector('us')
detector2 = gender.Detector()

def get_firstname(str):
    str = re.sub(" - "," ",str)
    str = re.sub("[^a-zA-Z-]"," ",str)
    str = re.sub("\s+"," ",str.lower().strip())
    firstname = str.split(" ")[0]
    if firstname in ["ms","mr","miss","mrs","dr", "rev", "reverend","professor","prof","md"] and len(str.split(" "))>1: firstname =  str.split(" ")[1]
    return firstname

def get_gender_from_free_apis(str):
    try:
        gender_str = detector2.get_gender(str)
        if "andy" in gender_str: gender_str = detector1.guess(str)
        if "unknown" in gender_str: gender_str = Genderizer.detect(firstName = str)
        if gender_str is None: return None
        if "female" in gender_str: return False
        if "male" in gender_str: return True
    except:
        pass
    return None

def get_gender_from_bing(str):
    url = "http://search.yahoo.com/search?q=facebook.com:%20" + str
    headers ={'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=headers)
    response_text = response.text.lower()
    male_indicators = response_text.count(" he ") + response_text.count(" his ")
    female_indicators = response_text.count(" she ") + response_text.count(" her ")
    if female_indicators>male_indicators: return False
    if male_indicators>female_indicators: return True
    return None

def get_gender(str):
    gender = get_gender_from_free_apis(str)
    #if gender is None: gender = get_gender_from_bing(str)
    return gender


# genders = pandas.read_csv('https://s3.amazonaws.com/advisorconnect-bigfiles/raw/prospects.txt', usecols=["id","name"], sep="\t")
# genders = genders[genders.name.notnull()]
# genders["firstname"] = genders.name.apply(get_firstname)
# unique_names = genders.drop_duplicates(subset="firstname")
# unique_names.to_csv("unique_names.csv", columns=["firstname"])
# genders.to_csv("prospect_firstnames.csv", columns=["id","firstname"])

unique_names = pandas.read_csv("unique_names.csv")
names = list(unique_names.firstname.values)
unique_names = None

pool = multiprocessing.Pool(150)
genders = pool.map(get_gender, names)
genders_dict = dict(zip(names,genders))

prospect_firstnames = pandas.read_csv("prospect_firstnames.csv")
prospect_firstnames["isMale"] = prospect_firstnames.firstname.apply(lambda x: genders_dict.get(x))
prospect_firstnames[prospect_firstnames.isMale.notnull()].to_csv("prospect_gender.csv", index=False, columns=["id","isMale"])

ambiguous_names = prospect_firstnames[prospect_firstnames.isMale.isnull()].drop_duplicates(subset="firstname")
ambiguous_names.to_csv("ambiguous_gender.csv", index=False, columns=["firstname"])




