import argparse
import psycopg2
import sys
import os
import requests
import datetime
import logging
import json
from itertools import islice
from dateutil import parser

from prime.prospects import models
from prime import create_app

from flask.ext.sqlalchemy import SQLAlchemy
from config import config

app_env = config[os.getenv('AC_CONFIG', 'beta')].SQLALCHEMY_DATABASE_URI
conn = psycopg2.connect(app_env)
cur = conn.cursor()

def export(id, path):
    os.chdir("training_data")
    try:
        os.mkdir(id)
    except:
        pass

    #Export schools
    schools = "copy (select * from (select school_id as s_id \
            from education where prospect_id={}) as educations \
            inner join school on school.id=educations.s_id) TO STDOUT with CSV DELIMITER E'\t' \
            HEADER;"

    #Export companies
    companies = "copy (select * from (select company_id as c_id \
            from job where prospect_id={}) as jobs inner join \
            company on company.id=jobs.c_id) TO STDOUT \
            with CSV DELIMITER E'\t' HEADER;"

    #Export jobs
    jobs = "copy (select * from (select company_id as c_id from job \
            where prospect_id={}) as c_ids inner join job on \
            job.company_id=c_ids.c_id) TO STDOUT with \
            CSV DELIMITER E'\t' HEADER;"

    #Export schools
    educations = "copy (select * from (select school_id as e_id \
            from education where prospect_id={}) as e_ids \
            inner join education on education.school_id=e_ids.e_id) TO STDOUT \
            with CSV DELIMITER E'\t' HEADER;"

    #Export people from jobs
    prospect_jobs = "copy (select * from (select prospect_id from \
            (select company_id as e_id from job where prospect_id={}) \
            as e_ids inner join job on job.company_id=e_ids.e_id) as p \
            inner join prospect on prospect.id=p.prospect_id) TO STDOUT \
            with CSV DELIMITER E'\t' HEADER;"

    prospect_schools = "copy (select * from (select prospect_id from \
            (select school_id as e_id from education where \
            prospect_id={}) as e_ids inner join education on \
            education.school_id=e_ids.e_id) as p inner join prospect on \
            prospect.id=p.prospect_id) TO STDOUT with CSV DELIMITER E'\t' HEADER;"


    school_file = open('{}/training_data/{}/schools.csv'.format(path, id), "w+")
    company_file = open('{}/training_data/{}/companies.csv'.format(path, id), "w+")
    educations_file = open('{}/training_data/{}/educations.csv'.format(path,id), "w+")
    jobs_file = open('{}/training_data/{}/jobs.csv'.format(path, id), "w+")
    prospect_schools_file = open('{}/training_data/{}/prospect_schools.csv'.format(path, id), "w+")
    prospect_jobs_file = open('{}/training_data/{}/prospect_jobs.csv'.format(path, id), "w+")

    cur.copy_expert(schools.format(id), school_file)
    cur.copy_expert(companies.format(id), company_file)
    cur.copy_expert(jobs.format(id), jobs_file)
    cur.copy_expert(educations.format(id), educations_file)
    cur.copy_expert(prospect_jobs.format(id, path), prospect_jobs_file)
    cur.copy_expert(prospect_schools.format(id, path), prospect_schools_file)

    school_file.close()
    company_file.close()
    educations_file.close()
    jobs_file.close()
    prospect_jobs_file.close()
    prospect_schools_file.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('id')
    parser.add_argument('path')
    args = parser.parse_args()
    export(args.id, args.path)


