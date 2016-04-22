from prime.utils.crawlera import reformat_crawlera

from gcloud.bigtable.happybase import Connection
import json
from gcloud.bigtable.client import Client
import os

PEOPLE_TABLE = 'people'
URL_TABLE = 'urls'
LINKEDIN_ID_TABLE = "linkedin_ids"
NAME_HEADLINE_TABLE = "name_headline"
COMPANY_TABLE = 'company'
COMPANY_LINKEDIN_ID_TABLE = "company_linkedin_ids"
COMPANY_URL_TABLE = "company_urls"
ALSO_VIEWED_REVERSE_TABLE = 'also_viewed_reverse'

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "gcloud-credentials.json"

def get_person_by_key(key):
    client = None
    try:
        client = Client(project='advisorconnect-1238')
        client.start()
        clust = client.cluster('us-central1-b', 'crawlera')        
        connection = Connection(cluster=clust)
    except Exception, e:
        if client and client.is_started():
            client.stop()
        print str(e)
        print "unable to connect to the database"
        return {}
    table = connection.table(PEOPLE_TABLE)
    row = table.row(key)
    if not row:
        connection.close()
        client.stop()
        return {}
    row = json.loads(row.values()[0])
    row = reformat_crawlera(row)
    connection.close()
    client.stop()
    return row

def get_person(url=None, linkedin_id=None, name=None, headline=None):
    if (not url and not linkedin_id) and (not headline or not name):
        return {}
    client = None
    try:
        client = Client(project='advisorconnect-1238')
        client.start()
        clust = client.cluster('us-central1-b', 'crawlera')              
        connection = Connection(cluster=clust)
    except Exception, e:
        if client and client.is_started():
            client.stop()        
        print str(e)
        print "unable to connect to the database"
        return {}
    if url:
        key = url.replace("https://","http://")
        table = connection.table(URL_TABLE)
    elif linkedin_id:
        key = linkedin_id
        table = connection.table(LINKEDIN_ID_TABLE)
    elif headline and name:
        key = name + headline
        table = connection.table(NAME_HEADLINE_TABLE)
    person_key = table.row(key)
    if not person_key:
        connection.close()
        client.stop()
        return {}    
    person_key = person_key.values()[0]
    connection.close()
    client.stop()
    return get_person_by_key(person_key)

def get_people_viewed_also(url=None):
    if not url:
        return []
    client = None
    try:
        client = Client(project='advisorconnect-1238')
        client.start()
        clust = client.cluster('us-central1-b', 'crawlera')              
        connection = Connection(cluster=clust)
    except Exception, e:
        if client and client.is_started():
            client.stop()        
        print str(e)
        print "unable to connect to the database"
        return []
    url = url.replace("https://","http://")
    table = connection.table(ALSO_VIEWED_REVERSE_TABLE)
    rows = table.cells(url, 'crawlera:unique_id', versions=100, include_timestamp=False)
    if not rows:
        connection.close()
        client.stop()
        return []
    output_rows = []
    for person_key in set(rows):
        person = get_person_by_key(person_key)
        output_rows.append(person)
    connection.close()
    client.stop()
    return output_rows

def get_company_by_key(key):
    client = None
    try:
        client = Client(project='advisorconnect-1238')
        client.start()
        clust = client.cluster('us-central1-b', 'crawlera')              
        connection = Connection(cluster=clust)
    except Exception, e:
        if client and client.is_started():
            client.stop()        
        print str(e)
        print "unable to connect to the database"
        return {}
    table = connection.table(COMPANY_TABLE)
    row = table.row(key)
    if not row:
        connection.close()
        client.stop()
        return {}    
    row = json.loads(row.values()[0])
    connection.close()
    client.stop()
    return row

def get_company(url=None, linkedin_id=None):
    if not url and not linkedin_id:
        return {}
    client = None
    try:
        client = Client(project='advisorconnect-1238')
        client.start()
        clust = client.cluster('us-central1-b', 'crawlera')              
        connection = Connection(cluster=clust)
    except Exception, e:
        if client and client.is_started():
            client.stop()        
        print str(e)
        print "unable to connect to the database"
        return {}
    if url:
        key = url.replace("https://","http://")
        table = connection.table(COMPANY_URL_TABLE)
    else:
        key = linkedin_id
        table = connection.table(COMPANY_LINKEDIN_ID_TABLE)
    company_key = table.row(key)
    if not company_key:
        connection.close()
        client.stop()
        return {}
    company_key = company_key.values()[0]
    connection.close()
    client.stop()
    return get_company_by_key(company_key)






