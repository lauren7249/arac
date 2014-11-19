from flask import Flask
from flask import render_template, request

from models import Session, Prospect, Job, Education

from consume import url_to_key

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast


session = Session()

app = Flask(__name__)
app.debug = True
app.config['DEBUG'] = True

SCHOOL_SQL = """\
select prospect.name, school_raw, end_date, degree, prospect.location_raw, prospect.industry_raw \
from ( \
select * from ( \
select id AS school_id, end_date, prospect_school.user as \
prospect_school_user, school_raw, degree \
from prospect_school where school_raw='%s' \
) as SCHOOLS \
where to_char(end_date, 'YYYY')='%s'\
) AS YEARS \
inner join prospect on prospect.id=prospect_school_user;\
"""

@app.route("/")
def search_schools():
    school_results = None
    if request.args.get("url"):
        s3_key = url_to_key(request.args.get("url"))
        #s3_key = "http:www.linkedin.compubjoey-petracca46941201"
        #s3_key = request.POST.GET("s3_key", "")
        prospect = session.query(Prospect).filter_by(s3_key=s3_key).first()
        schools = session.query(Education).filter_by(user=prospect.id)
        school_results = []
        for school in schools:
            print SCHOOL_SQL % (school.school_raw, school.end_date.year)
            school_prospects = session.execute(SCHOOL_SQL % (school.school_raw, school.end_date.year))
            for prospect in school_prospects:
                result = {}
                result['name'] = prospect[0]
                result['school'] = prospect[1]
                result['end_date'] = prospect[2]
                result['degree'] = prospect[3]
                result['current_location'] = prospect[4]
                result['industry'] = prospect[5]
                school_results.append(result)
    return render_template('home.html', school_results=school_results)

JOB_SQL = """select prospect.name, company_raw, start_date, end_date, \
job_location, propsect.location_raw, propsect.industry_raw \
from (select * from (\
select id as job_id, start_date, end_date, job.user as job_user, company_raw,location as job_location \
from job where company_raw='%s') as JOBS \
where to_char(start_date, 'YYYY') between '%s' and '%s' OR \
to_char(end_date, 'YYYY') between '%s' and '%s') AS YEARS \
INNER JOIN prospect on prospect.id=job_user;\
"""

@app.route("/jobs")
def search_jobs():
    job_results = None
    if request.args.get("url"):
        s3_key = url_to_key(request.args.get("url"))
        prospect = session.query(Prospect).filter_by(s3_key=s3_key).first()
        jobs = session.query(Job).filter_by(user=prospect.id)
        job_results = []
        for job in jobs:
            print JOB_SQL % (job.company_raw, job.start_date, job.end_date,\
                        job.start_date, job.end_date)
            if job.end_date:
                job_prospects = session.execute(JOB_SQL %\
                        (job.company_raw, job.start_date, job.end_date,\
                        job.start_date, job.end_date))
            else:
                job_prospects = session.execute(JOB_SQL %\
                        (job.company_raw, job.start_date, "2014",\
                        job.start_date, "2014"))
            for prospect in job_prospects:
                result = {}
                result['name'] = prospect[0]
                result['company'] = prospect[1]
                result['start_date'] = prospect[2]
                result['end_date'] = prospect[3]
                result['job_location'] = prospect[4]
                result['current_location'] = prospect[5]
                result['industry'] = prospect[6]
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

