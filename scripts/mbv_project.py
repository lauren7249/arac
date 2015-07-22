
from prime.utils.googling import *
from prime.utils import *
from prime.prospects.models import *
from prime.prospects.get_prospect import session
import pandas

#raw list of values from client
schools = ["University of California, Berkeley (UC Berkeley)", "University of Texas, Austin",  "Texas A&M University, College Station", "University of Michigan, Ann Arbor (U-M)",  "Penn State University Park", "Northwestern University (NU)", "University of Pennsylvania", "Boston University", "Stanford University",  "University of Notre Dame", "University of Minnesota, Twin Cities", "Universidad de Puerto Rico, Mayagüez (UPRM)", "University of Southern California (USC)", "University of California, Los Angeles (UCLA)"]

#normalize names to database values
school_names = [] 
for school in schools:
	name = normalize_school_name(school)
	school_names.append(name)

school_ids = []
for name in school_names:
	school = session.query(School).filter_by(name=name).first()
	if school is not None:
		school_ids.append(school.id)

#check arachnid/mvb_query.sql for query to generate output. exported manually

mvb = pandas.read_csv("/Users/lauren/documents/mvb.csv", delimiter="|")

#filter columns
mvb = mvb[['school_id', 'prospect_id', 'degree', 'start_date',
       'end_date', 'name', 'url', 'name.1', 'linkedin_id',
       'location_raw', 'industry',
       'connections']]

#clean degree
mvb.degree = mvb.degree.replace(to_replace="\n", value=" | ", regex=True)
mvb.dropna(subset=["degree"], inplace=True)

#calculate years in school
mvb.end_date = pandas.to_datetime(mvb.end_date)
mvb.start_date = pandas.to_datetime(mvb.start_date)
mvb["duration_in_school"] = mvb.end_date - mvb.start_date
mvb.duration_in_school= mvb.duration_in_school/numpy.timedelta64(1, 'Y')

#filter to 4-year degrees
mvb[3.5 < mvb.duration_in_school][mvb.duration_in_school < 4.5]

#export
mvb.to_csv("/Users/lauren/documents/mvb_clean.csv")
#https://mail.google.com/mail/u/0/#sent/14eb28e65dec69c3