import re
from flask import Flask
import urllib

from . import prospects
from prime.prospects.models import Prospect, Job, Education
from prime import db

#from consume.consume import generate_prospect_from_url
#from consume.convert import clean_url

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast


class ProspectList(object):

    session = db.session

    SCHOOL_SCORE = 0.6
    SCHOOL_DEGREE_SCORE = 1.0

    JOB_SCORE = 0.7
    JOB_LOCATION_SCORE = 0.9
    JOB_GROUP_SCORE = 1.5

    def __init__(self, prospect, *args, **kwargs):

        self.prospect = prospect
        self.prospect_jobs = session.query(Job).filter_by(user=prospect.id)
        self.prospect_schools = session.query(Education).filter_by(user=prospect.id)
        self.results = {}

    def _get_school(self, school):
        """
        We are going to get everyone who went to the same school during the same
        time period.
        """

        SCHOOL_SQL = """\
        select prospect.name, school_raw, end_date, degree, prospect.location_raw, \
        prospect.industry_raw, prospect.url, prospect.id as prospect_id \
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
        end_date = school.end_date.year if school.end_date else "2000"
        school_prospects = session.execute(SCHOOL_SQL % (school.school_raw, end_date))

        for prospect in school_prospects:
            #Check if they worked at the same location
            if prospect[3] == prospect_degree:
                prospect.append(SCHOOL_DEGREE_SCORE)
            else:
                prospect.append(SCHOOL_SCORE)
        return job_prospects

    def _set_schools(self):
        for prospect_school in self.prospect_schools:
            schools = self._get_school(prospect_school)
            for school in schools:
                id = school[7]
                score = school[8]
                result = {"name":school[0],
                            "company": school[1],
                            "end_date": school[2],
                            "degree": school[3],
                            "current_location": school[4],
                            "industry": school[5],
                            "url": school[6],
                            "id": id}
                exisiting  = self.results.get(id)
                if exisiting:
                    score += exisiting.get("score")
                self.results[id] = {"score":score,
                                    "school":result}
        return True


    def _get_job(self, job):
        """
        Get all prospects who worked at the same job at the same time
        """

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
        prospect_location = job.location
        prospect_group = None #TODO
        start_date = job.start_date.year if job.start_date else "2000"
        end_date = job.end_date.year if job.end_date else "2015"
        job_prospects = session.execute(JOB_SQL %\
                (job.company_raw, start_date,\
                end_date, start_date,\
                end_date))
        for prospect in job_prospects:
            #Check if they worked at the same location
            if prospect[4] == prospect_location:
                prospect.append(JOB_LOCATION_SCORE)
            else:
                prospect.append(JOB_SCORE)
        return job_prospects


    def _set_jobs(self):
        for prospect_job in self.prospect_jobs:
            jobs = self._get_job(prospect_job)
            for job in jobs:
                id = job[8]
                score = job[9]
                result = {"name":job[0],
                            "company": job[1],
                            "start_date": job[2],
                            "end_date": job[3],
                            "job_location": job[4],
                            "current_location": job[5],
                            "industry": job[6],
                            "url": job[7],
                            "id": id,
                            "type": "job"}
                exisiting  = self.results.get(id)
                if exisiting:
                    score += exisiting.get("score")
                self.results[id] = {"score": score,
                                    "jobs":result}
        return True


    def calculate_score(self):
        print "Getting Schools"
        schools = self._set_schools()
        print "Getting Jobs"
        jobs = self._set_jobs()
        return self.results


