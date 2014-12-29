from flask import Flask
import urllib
from flask import render_template, request

from . import prospects
from prime.prospects.models import Prospect, Job, Education
from prime.prospects.prospect_list import ProspectList
from prime import db

from consume.consume import generate_prospect_from_url
from consume.convert import clean_url

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast


session = db.session


@prospects.route("/")
def search():
    results = None
    if request.args.get("url"):
        raw_url = urllib.unquote(request.args.get("url")).decode('utf8')
        url = clean_url(raw_url)
        prospect = generate_prospect_from_url(url)
        prospect_list = ProspectList(prospect)
        results = prospect_list.get_results()
    return render_template('home.html', results=results)

JOB_SQL = """select prospect.name, company_raw, start_date, end_date, \
job_location, prospect.location_raw, prospect.industry_raw, prospect.url, \
prospect.id as prospect_id \
from (select * from (\
select id as job_id, start_date, end_date, job.user as job_user, company_raw,location as job_location \
from job where company_raw='%s') as JOBS \
where to_char(start_date, 'YYYY') between '%s' and '%s' OR \
to_char(end_date, 'YYYY') between '%s' and '%s') AS YEARS \
INNER JOIN prospect on prospect.id=job_user;\
"""

NO_YEAR_JOB_SQL = """select prospect.name, company_raw, start_date, end_date, \
job_location, prospect.location_raw, prospect.industry_raw, prospect.url, \
prospect.id as prospect_id \
from (\
select id as job_id, start_date, end_date, job.user as job_user, company_raw,location as job_location \
from job where company_raw='%s') as JOBS \
INNER JOIN prospect on prospect.id=job_user;\
"""

@prospects.route("/jobs")
def search_jobs():
    job_results = []
    if request.args.get("url"):
        raw_url = urllib.unquote(request.args.get("url")).decode('utf8')
        url = clean_url(raw_url)
        prospect = generate_prospect_from_url(url)
        jobs = session.query(Job).filter_by(user=prospect.id)
        job_results = []
        for job in jobs:
            start_date = job.start_date.year if job.start_date else "2000"
            end_date = job.end_date.year if job.end_date else "2015"
            print JOB_SQL % (job.company_raw, start_date,\
                    end_date, start_date,\
                    end_date)
            job_prospects = session.execute(JOB_SQL %\
                    (job.company_raw, start_date,\
                    end_date, start_date,\
                    end_date))
            for prospect in job_prospects:
                result = {}
                result['name'] = prospect[0]
                result['company'] = prospect[1]
                result['start_date'] = prospect[2]
                result['end_date'] = prospect[3]
                result['job_location'] = prospect[4]
                result['current_location'] = prospect[5]
                result['industry'] = prospect[6]
                result['url'] = prospect[7]
                result['id'] = prospect[8]
                job_results.append(result)
        if len(job_results) == 0:
            for job in jobs:
                job_prospects = session.execute(NO_YEAR_JOB_SQL % job.company_raw)
                for prospect in job_prospects:
                    result = {}
                    result['name'] = prospect[0]
                    result['company'] = prospect[1]
                    result['start_date'] = prospect[2]
                    result['end_date'] = prospect[3]
                    result['job_location'] = prospect[4]
                    result['current_location'] = prospect[5]
                    result['industry'] = prospect[6]
                    result['url'] = prospect[7]
                    result['id'] = prospect[8]
                    job_results.append(result)

    return render_template('home.html', job_results=job_results)


#linkedin_prospects
#linked_prospects = session.query(Prospect.id,\
#        Prospect.s3_key)\
#        .filter(Prospect.s3_key.in_(prospect.linked_profiles))
#school_propsects

print "made it"
"""
if __name__ == '__main__':
    try:
        app.run(debug=True)
    except Exception:
        app.logger.exception('Failed')
"""

