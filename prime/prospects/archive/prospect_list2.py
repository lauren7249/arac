import re, os
from pandas import *
from flask.ext.sqlalchemy import SQLAlchemy
from flask import Flask
import urllib
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from . import prospects
from prime.prospects.get_prospect import *
from prime.prospects.models import Prospect, Job, Education
from prime import db
from sklearn.externals import joblib
from prime.prospects.process_entity3 import *

#from consume.consume import generate_prospect_from_url
#from consume.convert import clean_url

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast

def setup():
    global predictors 
    global model
    AWS_KEY = os.environ["AWS_ACCESS_KEY_ID"]
    AWS_SECRET = os.environ["AWS_SECRET_ACCESS_KEY"]
    aws_connection = S3Connection(AWS_KEY, AWS_SECRET)
    bucket = aws_connection.get_bucket('advisorconnect-bigfiles')
    k = Key(bucket)
    k.key = "/models/GridSearchCV.model"
    k.get_contents_to_filename("model")
    model = joblib.load("model")

    k = Key(bucket)
    k.key = "/models/model_predictors"
    k.get_contents_to_filename("model_predictors")
    predictors = joblib.load("model_predictors")

def add_knowns(prospects_scored, prospect):
    try:
        k = Key(bucket)
        k.key = "entities/prospects/" +  str(prospect.id) + "/known_firstdegrees.csv"
        k.get_contents_to_filename("known_firstdegrees.csv")     
        known_firstdegrees_df = pandas.read_csv("known_firstdegrees.csv", delimiter=",", names=["name", "linkedin_id", "url"])
        known_firstdegrees_df.fillna(value="", inplace=True)
        for i, row in known_firstdegrees_df.iterrows():
            linkedin_id = row["linkedin_id"]
            url = row["url"]
            #print url
            pprospect = from_linkedin_id(linkedin_id)
            if prospect is None and len(url)>0:
                prospect = from_url(linkedin_id)
            if prospect is not None:
                prospect_id = prospect.id
                score = 100.0
                newrow = {"prospect_id":prospect_id, "score":score}
                prospects_scored = prospects_scored.append(newrow, ignore_index=True)
    except:
        pass

    try:
        k = Key(bucket)
        k.key = "entities/prospects/" +  str(prospect.id) + "/linkedin_ids.csv"
        k.get_contents_to_filename("linkedin_ids.csv")        
        known_firstdegrees_df = pandas.read_csv("linkedin_ids.csv", delimiter=",", names=["linkedin_id"])
        known_firstdegrees_df.fillna(value="", inplace=True)
        for i, row in known_firstdegrees_df.iterrows():
            linkedin_id = row["linkedin_id"]
            #print url
            prospect = from_linkedin_id(linkedin_id)
            if prospect is not None:
                prospect_id = prospect.id
                score = 100.0
                newrow = {"prospect_id":prospect_id, "score":score}
                prospects_scored = prospects_scored.append(newrow, ignore_index=True)
    except:
        pass

    try:
        k = Key(bucket)
        k.key = "entities/prospects/linkedin_id/" +  str(prospect.linkedin_id) + "/linkedin_ids.csv"
        k.get_contents_to_filename("linkedin_ids.csv")        
        known_firstdegrees_df = pandas.read_csv("linkedin_ids.csv", delimiter=",", names=["linkedin_id"])        
        known_firstdegrees_df.fillna(value="", inplace=True)
        for i, row in known_firstdegrees_df.iterrows():
            linkedin_id = row["linkedin_id"]
            #print url
            prospect = from_linkedin_id(linkedin_id)
            if prospect is not None:
                prospect_id = prospect.id
                score = 100.0
                newrow = {"prospect_id":prospect_id, "score":score}
                prospects_scored = prospects_scored.append(newrow, ignore_index=True)
    except:
        pass

    return prospects_scored

class ProspectList(object):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql://arachnid:devious8ob8@arachnid.cc540uqgo1bi.us-east-1.rds.amazonaws.com:5432/arachnid'
    db = SQLAlchemy(app)
    session = db.session
    def __init__(self, prospect, *args, **kwargs):

        self.prospect = prospect
        self.results = {}
        setup()

    def get_best_guesses(self):
        process_prospect(self.prospect.id)
        processed_df = None
        processed_files = list(bucket.list("entities/prospects/" + str(self.prospect.id) + "/processed_"))
        common_columns = []
        for key in processed_files:
            path = "https://s3.amazonaws.com/advisorconnect-bigfiles/" + key.name
            path = re.sub(' ','+',path)
            df = pandas.read_csv(path, delimiter=',', index_col=0)
            df.drop_duplicates(inplace=True)
            if processed_df is None:
                processed_df = df
            else:
                common_columns = list(processed_df.columns & df.columns)
                processed_df = processed_df.join(df, how='outer', lsuffix="_")
                for column in common_columns:
                    to_sum = processed_df.filter(regex="^"+column)
                    processed_df[column] = to_sum.sum(axis=1)
                    processed_df.drop(column+"_", axis=1, inplace=True)
        if processed_df is None: return results

        processed_df.fillna(value=0, inplace=True)

        missing_cols = list(set(predictors) - set(processed_df.columns))
        for missing_col in missing_cols:
            processed_df[missing_col] = 0

        y_pred = model.decision_function(processed_df[predictors])
        y = pandas.DataFrame(y_pred)
        y.columns = ["score"]

        prospect_ids = pandas.DataFrame(processed_df.index.get_values())
        prospect_ids.columns = ["prospect_id"]

        prospects_scored = pandas.concat([prospect_ids,y], axis=1)

        prospects_scored = add_knowns(prospects_scored)

        prospects_scored.drop_duplicates(cols='prospect_id', take_last=True, inplace=True)
        prospects_scored = prospects_scored.sort(columns="score", ascending=False).head(100)    
        return prospects_scored


    def get_results(self, restrict_to_knowns=False):
        results = []
        prospects_scored = pandas.DataFrame(columns=["prospect_id", "score"])
        prospects_scored = add_knowns(prospects_scored, self.prospect)
        if not restrict_to_knowns:
            prospects_scored = prospecs_scored.append(get_best_guesses())

        for index, row in prospects_scored.iterrows():
            prospect_id = int(row["prospect_id"])
            if prospect_id==self.prospect.id: continue
            prospect = from_prospect_id(prospect_id)

            common_schools = []
            for s in self.prospect.schools:
                for s2 in prospect.schools:
                    if s.school.id == s2.school.id: common_schools.append(s)
            common_jobs = []
            for j in self.prospect.jobs:
                for j2 in prospect.jobs:
                    if j.company.id == j2.company.id: common_jobs.append(j)

           # print common_schools
            #print common_jobs
            user = {}
            #user['end_date'] = end_date.strftime("%y") if end_date else None
            user['prospect_name'] = prospect.name
            user["s3_key"] = prospect.s3_key
            '''user["schools"] = self.prospect.schools
            user['jobs'] = self.prospect.jobs'''
            if len(common_schools)>0:
                user['school_name'] = common_schools[0].school.name
                user['school_id'] = common_schools[0].school_id

            if len(common_jobs)>0:
                user['title'] = common_jobs[0].title
                user['company_name'] = common_jobs[0].company.name
                user['company_id'] = common_jobs[0].company_id

            user['current_location'] = prospect.location_raw
            user['current_industry'] = prospect.industry_raw
            user['url'] = prospect.url
            #user['relationship'] = relationship
            user['score'] = row["score"]
            user['id'] = prospect_id
            user['image_url'] = prospect.image_url
            user["connections"] = prospect.connections
            user["salary"] = prospect.calculate_salary
            results.append(user)
        return results