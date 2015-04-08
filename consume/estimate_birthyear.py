

#if bachelors
	#if dates
		#when did they get their bachelors? assume when they were 22
	#else if work or grad school
		#when did they start working or start grad school? assume when they were 22
		#if no dates, count number of jobs and assume 2 years for each
	#else - no work or grad school, no dates for bachelors
		#assume still in school - 20

#else - no bachelors
	#assume started first job/degree when 18
	#if not dates count number of jobs and assume 2 years for each

def getYear(date):
    try:
        return int(date.split("-")[0])
    except:
        pass
    return None

def isBachelors(str):
	str = str.lower()
	if str.find("bachelor")>-1: return True
	if re.match("(\b|^)b\s*.*\s*s\s*.*\s*", str): return True
	if re.match("(\b|^)b\s*.*\s*a\s*.*\s*", str): return True
	if re.match("(\b|^)b\s*.*\s*eng\s*.*\s*", str): return True
	return False

import pandas, re

educations = pandas.read_csv('https://s3.amazonaws.com/advisorconnect-bigfiles/raw/educations.txt', usecols=["prospect_id","end_date","start_date","degree"], sep="\t")
bachelors = educations[educations.degree.notnull()]
bachelors["isBachelors"] = bachelors.degree.apply(isBachelors)
bachelors = bachelors[bachelors.isBachelors]
bachelors.end_date = bachelors.end_date.apply(getYear)
bachelors.start_date = bachelors.start_date.apply(getYear)
bachelors.to_csv("bachelors.csv", columns=["prospect_id","start_date","end_date"], index=False)
