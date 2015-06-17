from prime.prospects.get_prospect import *
from prime.prospects.models import ProspectGender
import pandas, datetime

prospect_path="for_insight_file.csv"
p = open(prospect_path,"ab")
p.write("prospect_id,location,industry,n_connections,estimated_income_level,is_male,amount")
p.write("\n")

session = get_session()

donors = pandas.read_csv("/mnt/big/donors_merged_onematch.csv")

def get_fields(row):
	prospect = from_prospect_id(row.prospect_id)
	gender = session.query(ProspectGender).get(row.prospect_id)
	if gender is not None: gender = gender.gender
	p.write(str(row.prospect_id) + ',"' + prospect.location_raw.encode('utf-8').strip() + '","' + prospect.industry_raw.encode('utf-8').strip() + '",' + str(prospect.connections) + "," + str(prospect.wealthscore) + "," + str(gender) + "," + str(row.amount))
	p.write("\n")

donors.apply(get_fields, axis=1)

ed = pandas.read_csv("https://s3.amazonaws.com/advisorconnect-bigfiles/raw/educations.txt",sep="\t")
donors_merged = donors.merge(ed, how="inner", on=["prospect_id"])
donors_ed = donors_merged[["prospect_id", 'school_id', 'degree', 'start_date', 'end_date']]
schools.columns = ["school_id","school"]
donors_ed = donors_ed.merge(schools, how="inner", on=["school_id"])
donors_ed.to_csv("for_insight_educations.csv", index=None)

jobs_path="for_insight_jobs.csv"
p = open(jobs_path,"ab")
p.write("prospect_id,company_id,company,job_location,title,start_date,end_date")
p.write("\n")
def get_jobs(row):
	jobs = session.query(Job).filter_by(prospect_id=row.prospect_id).all()
	for job in jobs:
		if job.location is None: job.location = ""
		if job.start_date is not None: start_date =job.start_date.strftime("%Y-%m-%d")
		else: start_date =""
		if job.end_date is not None: end_date = job.end_date.strftime("%Y-%m-%d")
		else: end_date=""
		p.write(str(row.prospect_id) + "," + str(job.company_id) + ',"' + job.company.name.encode('utf-8').strip() + '","' + job.location.encode('utf-8').strip() + '","' + job.title.encode('utf-8').strip() + '",' + start_date + "," + end_date)
		p.write("\n")

donors.apply(get_jobs, axis=1)

jobs = pandas.read_csv("for_insight_jobs.csv", error_bad_lines=False)
jobs.drop_duplicates(subset=["prospect_id","company_id","title","job_location"], inplace=True)
#364060
job_counts = pandas.read_csv("companies_with_count.txt", sep="\t")
job_counts = job_counts[["id","count"]]
job_counts.columns = ["company_id","company_size"]
jobs = jobs.merge(job_counts, on=["company_id"], how="inner")
#358734

jobs.to_csv("for_insight_jobs.csv", index=None)


