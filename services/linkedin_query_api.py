import psycopg2
import psycopg2.extras
import web
import json
from prime.utils.crawlera import reformat_crawlera

web.config.debug = False
urls = (
    '/get_person_by_url', 'get_person_by_url'
)

CONNECTION_STRING = "dbname='p200_production' user='arachnid' host='oracle' password='devious8ob8'"
PEOPLE_TABLE = 'people'
COMPANY_TABLE = 'companies'
app = web.application(urls, globals())
web_session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})


def get_people_viewed_also(url=None, version='1.0.0'):
    if version=='1.0.0':
        if not url:
            return []
        try:
            conn = psycopg2.connect(CONNECTION_STRING)
        except:
            print "unable to connect to the database"
            return []
        url = url.replace("https://","http://")
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        query = """SELECT * from %s where also_viewed @>'["%s"]'""" % (PEOPLE_TABLE, url)
        cur.execute(query)
        rows = cur.fetchall()
        if not rows:
            conn.close()
            return []
        output_rows = []
        for row in rows:
            out_row = dict(row)
            output = reformat_crawlera(out_row)
            output_rows.append(output)
        conn.close()
        return output_rows
    return []

def get_company(url=None, linkedin_id=None, version='1.0.0'):
    if version=='1.0.0':
        if not url and not linkedin_id:
            return {}
        try:
            conn = psycopg2.connect(CONNECTION_STRING)
        except:
            print "unable to connect to the database"
            return {}
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if url:
            url = url.replace("https://","http://")
            query = """SELECT * from %s where url='%s'""" % (COMPANY_TABLE, url)
        else:
            query = """SELECT * from %s where linkedin_id='%s'""" % (COMPANY_TABLE, linkedin_id)
        try:
            cur.execute(query)
            row = cur.fetchone()
            if not row:
                conn.close()
                return {}
            row = dict(row)
            conn.close()
            return row
        except:
            pass
    return {}

def get_person(url=None, linkedin_id=None, name=None, headline=None, version='1.0.0'):
    if version=='1.0.0':
        if (not url and not linkedin_id) and (not headline or not name):
            return {}
        try:
            conn = psycopg2.connect(CONNECTION_STRING)
        except:
            print "unable to connect to the database"
            return {}
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if url:
            url = url.replace("https://","http://")
            query = """SELECT * from %s where url='%s'""" % (PEOPLE_TABLE, url)
        elif linkedin_id:
            query = """SELECT * from %s where linkedin_id='%s'""" % (PEOPLE_TABLE, linkedin_id)
        elif headline and name:
            headline = headline.replace("'","''")
            name = name.replace("'","''")
            query = """SELECT * from %s where headline='%s' and full_name='%s' """ % (PEOPLE_TABLE, headline, name)
        cur.execute(query)
        row = cur.fetchone()
        if not row:
            conn.close()
            return {}
        row = dict(row)
        output = reformat_crawlera(row)
        conn.close()
        return output
    return {}

