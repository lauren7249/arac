import re, pandas
from flask import Flask
import urllib
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from . import prospects
from prime.prospects.models import Prospect, Job, Education
from prime import db
from sklearn.externals import joblib

#from consume.consume import generate_prospect_from_url
#from consume.convert import clean_url

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast

session = db.session
AWS_KEY = 'AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET = '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'
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
PROSPECT_SQL = """select * from prospect where id=%s;"""
class ProspectList(object):


    def __init__(self, prospect, *args, **kwargs):

        self.prospect = prospect
        self.results = {}

    def get_results(self):

        processed_dfs = []
        processed_files = list(bucket.list("by_prospect_id/" + str(self.prospect.id) + "/processed_"))
        for key in processed_files:
            path = "https://s3.amazonaws.com/advisorconnect-bigfiles/" + key.name
            df = pandas.read_csv(path, delimiter='\t', index_col=0)
            processed_dfs.append(df)

        processed_df = processed_dfs[0]
        if len(processed_dfs)>0:
            processed_df = processed_df.join(processed_dfs[1:], how='inner')

        y_pred = model.decision_function(processed_df[predictors])
        y = pandas.DataFrame(y_pred)
        y.columns = ["score"]

        prospect_ids = pandas.DataFrame(processed_df.index.get_values())
        prospect_ids.columns = ["prospect_id"]
        prospects_scored = pandas.concat([prospect_ids,y], axis=1)
        prospects_scored.sort(columns="prospect_id", ascending=False, inplace=True)

        results = []
        for index, row in prospects_scored.iterrows():
            prospect_id = int(row["prospect_id"])
            prospect = session.query(Prospect).get(prospect_id)
            #prospect = session.execute(PROSPECT_SQL % (prospect_id))[0]
            
            user = {}
            #user['end_date'] = end_date.strftime("%y") if end_date else None
            user['prospect_name'] = prospect.name
            #user['school_name'] = school_name
            #user['school_id'] = school_id
            #user['title'] = title
            #user['company_name'] = company_name
            #user['company_id'] = company_id            
            user['current_location'] = prospect.location_raw
            user['current_industry'] = prospect.industry_raw
            user['url'] = prospect.url
            #user['relationship'] = relationship
            user['score'] = row["score"]
            user['id'] = prospect_id
            user['image_url'] = prospect.image_url            
            results.append(user)
        return results
