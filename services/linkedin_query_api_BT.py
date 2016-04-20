from prime.utils.crawlera import reformat_crawlera

from gcloud.bigtable.happybase import Connection
import json
from gcloud.bigtable.client import Client

PEOPLE_TABLE = 'people'
URL_TABLE = 'urls'
LINKEDIN_ID_TABLE = "linkedin_ids"
NAME_HEADLINE_TABLE = "name_headline"
COMPANY_TABLE = 'company'
ALSO_VIEWED_REVERSE_TABLE = 'also_viewed_reverse'

cl = Client(project='advisorconnect-1238')
clust = cl.cluster('us-central1-b', 'crawlera')

def get_person_by_key(key):
    try:
        connection = Connection(cluster=clust)
    except:
        print "unable to connect to the database"
        return {}
    table = connection.table(PEOPLE_TABLE)
    row = table.row(key)
    row = json.loads(row.values()[0])
    # row = reformat_crawlera(row)
    connection.close()
    return row

def get_person(url=None, linkedin_id=None, name=None, headline=None):
    if (not url and not linkedin_id) and (not headline or not name):
        return {}
    try:
        connection = Connection(cluster=clust)
    except:
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
    person_key = person_key.values()[0]
    connection.close()
    return get_person_by_key(person_key)

# def get_people_viewed_also(url=None, version='1.0.0'):
#     if version=='1.0.0':
#         if not url:
#             return []
#         try:
#             conn = psycopg2.connect(CONNECTION_STRING)
#         except:
#             print "unable to connect to the database"
#             return []
#         url = url.replace("https://","http://")
#         cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#         query = """SELECT * from %s where also_viewed @>'["%s"]'""" % (PEOPLE_TABLE, url)
#         cur.execute(query)
#         rows = cur.fetchall()
#         if not rows:
#             conn.close()
#             return []
#         output_rows = []
#         for row in rows:
#             out_row = dict(row)
#             output = reformat_crawlera(out_row)
#             output_rows.append(output)
#         conn.close()
#         return output_rows
#     return []

# def get_company(url=None, linkedin_id=None, version='1.0.0'):
#     if version=='1.0.0':
#         if not url and not linkedin_id:
#             return {}
#         try:
#             conn = psycopg2.connect(CONNECTION_STRING)
#         except:
#             print "unable to connect to the database"
#             return {}
#         cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#         if url:
#             url = url.replace("https://","http://")
#             query = """SELECT * from %s where url='%s'""" % (COMPANY_TABLE, url)
#         else:
#             query = """SELECT * from %s where linkedin_id='%s'""" % (COMPANY_TABLE, linkedin_id)
#         try:
#             cur.execute(query)
#             row = cur.fetchone()
#             if not row:
#                 conn.close()
#                 return {}
#             row = dict(row)
#             conn.close()
#             return row
#         except:
#             pass
#     return {}




