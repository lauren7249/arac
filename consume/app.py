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
select prospect.name, school_raw, end_date, degree, prospect.location, prospect.industry \
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
def search():
    school_results = None
    if request.args.get("url"):
        s3_key = url_to_key(request["url"])
        #s3_key = "http:www.linkedin.compubjoey-petracca46941201"
        #s3_key = request.POST.GET("s3_key", "")
        prospect = session.query(Prospect).filter_by(s3_key=s3_key).first()
        schools = session.query(Education).filter_by(user=prospect.id)
        school_results = []
        for school in schools:
            school_prospects = session.execute(SCHOOL_SQL % (school, school.end_date.year))
            for prospect in school_propsects:
                result = {}
                result['name'] = prospect[0]
                result['school'] = prospect[1]
                result['end_date'] = prospect[2]
                result['degree'] = prospect[3]
                result['current_location'] = prospect[4]
                result['industry'] = prospect[5]
                school_results.append(result)

    return render_template('home.html', school_results=school_results)


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

