
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

#export
mvb.to_csv("/Users/lauren/documents/mvb_clean.csv")
#https://mail.google.com/mail/u/0/#sent/14eb28e65dec69c3