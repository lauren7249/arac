import pandas
import re
from prime.processing_service.constants import facebook_re, email_re
from prime.processing_service.pipl_service import PiplService, PiplFacebookService
from prime.processing_service.clearbit_service_webhooks import ClearbitPersonService
from prime.processing_service.helper import sort_social_accounts, flatten

inpath = "~/arachnid/aweber_intro_export.csv"
outpath = "aweber_output.csv"
N_ROWS = 99999

def get_id_columns(inpath):
    df = pandas.read_csv(inpath, nrows=100)
    df.fillna("", inplace=True)
    columns = df.columns.values
    facebook_column = {}
    email_column = {}
    for index, row in df.iterrows():
        for column in columns:
            if isinstance(row[column], basestring):
                if re.search(email_re, row[column]): email_column[column] = email_column.get(column,0) + 1  
                if re.search(facebook_re, row[column]): facebook_column[column] = facebook_column.get(column,0) + 1 
    if facebook_column:
        facebook_column = sorted(facebook_column,  reverse=True)[0]
    else: 
        facebook_column=None
    if email_column:
        email_column = sorted(email_column,  reverse=True)[0]
    else:
        email_column = None
    return email_column, facebook_column

def get_username_lists(inpath):
    email_column, facebook_column = get_id_columns(inpath)
    df = pandas.read_csv(inpath, nrows=N_ROWS)[[email_column, facebook_column]]
    df.fillna("", inplace=True)    
    emails = []
    facebooks = []
    for index, row in df.iterrows():
        emails.append({row[email_column]:{}})
        username = row[facebook_column].split("/")[-1]
        facebooks.append({username:{}})
    return emails, facebooks

def enrich(inpath, outpath):
    emails, facebooks = get_username_lists(inpath)
    emails = PiplService(None, emails).multiprocess()
    emails = ClearbitPersonService(None, emails).multiprocess()
    facebooks = PiplFacebookService(None, facebooks).multiprocess()
    df = pandas.read_csv(inpath, nrows=N_ROWS, encoding = "ISO-8859-1")
    df.fillna("", inplace=True)     
    in_columns = df.columns.values
    out_columns = set()
    outdf = pandas.DataFrame()
    for index, row in df.iterrows():
        emails_data = emails[index].values()[0]
        facebook_data = facebooks[index].values()[0]
        social_accounts = sort_social_accounts( emails_data.get("social_accounts",[]) + facebook_data.get("social_accounts",[]))
        clearbit_fields = flatten(emails_data.get("clearbit_fields",{}))
        outrow = {}
        outrow.update(clearbit_fields)
        outrow.update(social_accounts)
        outrow.pop("employment_domain",None)
        out_columns.update(outrow.keys())
        outrow.update(dict(row))      
        outdf = outdf.append(outrow, ignore_index=True)
    out_columns = list(out_columns)
    out_columns.sort()
    outdf.to_csv(path_or_buf=outpath, index=False, columns=list(in_columns) + out_columns, encoding='utf-8')

if __name__=="__main__":
    enrich(inpath, outpath)
    #print emails
    #print facebooks