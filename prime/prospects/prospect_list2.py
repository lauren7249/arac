import re, pandas
from flask import Flask
import urllib
from boto.s3.connection import S3Connection
from . import prospects
from prime.prospects.models import Prospect, Job, Education
from prime import db

#from consume.consume import generate_prospect_from_url
#from consume.convert import clean_url

from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy import select, cast

session = db.session
AWS_KEY = 'AKIAIWG5K3XHEMEN3MNA'
AWS_SECRET = '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'
aws_connection = S3Connection(AWS_KEY, AWS_SECRET)
bucket = aws_connection.get_bucket('advisorconnect-bigfiles')

class ProspectList(object):


    def __init__(self, prospect, *args, **kwargs):

        self.prospect = prospect
        self.results = {}

    def get_results(self):
        results = []

        processed_dfs = []
        processed_files = list(bucket.list("by_prospect_id/" + str(self.prospect.id) + "/processed_"))
        for key in processed_files:
            path = "https://s3.amazonaws.com/advisorconnect-bigfiles/" + key.name
            df = pandas.read_csv(path, delimiter='\t', index_col=0)
            processed_dfs.append(df)

        processed_df = processed_dfs[0]
        if len(processed_dfs)>0:
            processed_df = processed_df.join(processed_dfs[1:], how='inner')

        print processed_df
        '''
        for result in raw_results:
            user = {}
            user['end_date'] = end_date.strftime("%y") if end_date else None
            user['prospect_name'] = prospect_name
            user['school_name'] = school_name
            user['school_id'] = school_id
            user['title'] = title
            user['company_name'] = company_name
            user['company_id'] = company_id            
            user['current_location'] = current_location
            user['current_industry'] = current_industry
            user['url'] = url
            user['relationship'] = relationship
            user['score'] = score
            user['id'] = id
            user['image_url'] = image_url            
            results.append(user)
        return sorted(results, key=lambda x:x['score'], reverse=True)
        '''



