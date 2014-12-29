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

session = db.session

SCHOOL_SCORE = 0.6
SCHOOL_DEGREE_SCORE = 1.0
JOB_SCORE = 0.7
JOB_LOCATION_SCORE = 0.9
JOB_GROUP_SCORE = 1.5

class ProspectList(object):


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
        prospect_degree = school.degree
        end_date = school.end_date.year if school.end_date else "2000"
        school_prospects = session.execute(SCHOOL_SQL % (school.school_raw, end_date))
        prospects = []
        for prospect in school_prospects:
            #Check if they worked at the same location
            prospect = [p for p in prospect]
            if prospect[3] == prospect_degree:
                prospect.append(SCHOOL_DEGREE_SCORE)
            else:
                prospect.append(SCHOOL_SCORE)
            prospects.append(prospect)
        return prospects

    def _set_schools(self):
        for prospect_school in self.prospect_schools:
            schools = self._get_school(prospect_school)
            for school in schools:
                id = school[7]
                score = school[8]
                result = {"name":school[0],
                            "school": school[1],
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
        prospects = []
        for prospect in job_prospects:
            #Check if they worked at the same location
            prospect = [p for p in prospect]
            if prospect[4] == prospect_location:
                prospect.append(JOB_LOCATION_SCORE)
            else:
                prospect.append(JOB_SCORE)
            prospects.append(prospect)
        return prospects


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


    def _calculate_score(self):
        print "Getting Schools"
        schools = self._set_schools()
        print "Getting Jobs"
        jobs = self._set_jobs()
        return self.results.items()

    def _organize_job(self, user, jobs, score, id):
        start_date = jobs.get("start_date")
        end_date = jobs.get("end_date", "Present")
        prospect_name = jobs.get("name")
        company_name = jobs.get("company")
        current_location = jobs.get("current_location")
        current_industry = jobs.get("industry")
        url = jobs.get("url")
        if start_date:
            relationship = "Worked together at {} from {} to\
            {}".format(company_name, start_date, end_date)
        else:
            relationship = "Worked together at {}".format(\
                    company_name, start_date, end_date)
        user['start_date'] = start_date
        user['end_date'] = end_date
        user['prospect_name'] = prospect_name
        user['company_name'] = company_name
        user['current_location'] = current_location
        user['current_industry'] = current_industry
        user['url'] = url
        user['relationship'] = relationship
        user['score'] = score
        user['id'] = id
        return user

    def _organize_school(self, user, schools, score, id):
        end_date = schools.get("end_date", "Present")
        prospect_name = schools.get("name")
        school_name = schools.get("school")
        current_location = schools.get("current_location")
        current_industry = schools.get("industry")
        url = schools.get("url")
        relationship = "Went to school together at {} in {}"\
                .format(school_name, end_date)
        user['end_date'] = end_date
        user['prospect_name'] = prospect_name
        user['school'] = school_name
        user['current_location'] = current_location
        user['current_industry'] = current_industry
        user['url'] = url
        user['relationship'] = relationship
        user['score'] = score
        user['id'] = id
        return user

    def get_results(self):
        results = []
        raw_results = self._calculate_score()
        for result in raw_results:
            user = {}
            id = result[0]
            score = result[1].get("score")
            jobs = result[1].get("jobs")
            schools = result[1].get("schools")
            if jobs:
                user = self._organize_job(user, jobs, score, id)
                if user.get("url") != self.prospect.url:
                    results.append(user)
            if schools:
                user = self._organize_jschool(user, schools, score, id)
                if user.get("url") != self.prospect.url:
                    results.append(user)
        return sorted(results, key=lambda x:x['score'], reverse=True)



