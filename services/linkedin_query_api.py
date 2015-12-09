import psycopg2
import psycopg2.extras
import web
import json
from prime.utils.crawlera import reformat_crawlera

web.config.debug = False
urls = (
    '/get_person_by_url', 'get_person_by_url'
)

CONNECTION_STRING = "dbname='ac_labs' user='arachnid' host='babel.priv.advisorconnect.co' password='devious8ob8'"
PEOPLE_TABLE = 'people'
COMPANY_TABLE = 'crawlera_linkedin_companies'
app = web.application(urls, globals())
web_session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})

def get_people(urls=[], version='1.0.0'):
    if version=='1.0.0':
        if not urls:
            return None
        try:
            conn = psycopg2.connect(CONNECTION_STRING)
        except:
            print "unable to connect to the database"
            return []
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        urls_string = "('" + "','".join(urls) + "')"
        query = """SELECT * from %s where url in %s""" % (PEOPLE_TABLE, urls_string)
        cur.execute(query)
        rows = cur.fetchall()
        if not rows:
            return []
        output_rows = []
        for row in rows:
            out_row = dict(row)
            output = reformat_crawlera(out_row)
            output_rows.append(output)
        return output_rows
    return []

def get_people_viewed_also(url=None, version='1.0.0'):
    return []
    if version=='1.0.0':
        if not url:
            return None
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
            return []
        output_rows = []
        for row in rows:
            out_row = dict(row)
            output = reformat_crawlera(out_row)
            output_rows.append(output)
        return output_rows
    return []

def get_company(url=None, linkedin_id=None, version='1.0.0'):
    if version=='1.0.0':
        if not url and not linkedin_id:
            return None
        try:
            conn = psycopg2.connect(CONNECTION_STRING)
        except:
            print "unable to connect to the database"
            return {}
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if url:
            url = url.replace("https://","http://")
            query = """SELECT * from %s where company_json @> '{"url": "%s"}'""" % (COMPANY_TABLE, url)
        else:
            query = """SELECT * from %s where company_json @> '{"linkedin_id": "%s"}'""" % (COMPANY_TABLE, linkedin_id)
        cur.execute(query)
        row = cur.fetchone()
        if not row:
            return {}
        row = dict(row).get("company_json")
        return row
    return {}

def get_person(url=None, linkedin_id=None, version='1.0.0'):
    if version=='1.0.0':
        if not url and not linkedin_id:
            return None
        try:
            conn = psycopg2.connect(CONNECTION_STRING)
        except:
            print "unable to connect to the database"
            return {}
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if url:
            url = url.replace("https://","http://")
            query = """SELECT * from %s where url='%s'""" % (PEOPLE_TABLE, url)
        else:
            query = """SELECT * from %s where linkedin_id='%s'""" % (PEOPLE_TABLE, linkedin_id)
        cur.execute(query)
        row = cur.fetchone()
        if not row:
            return {}
        row = dict(row)
        output = reformat_crawlera(row)
        return output
    return {}

class get_person_by_url:
    def POST(self):
        d = json.loads(web.data())
        url = d.get("url","")
        version = d.get("api_version")
        person = get_profile_by_any_url(url)
        return json.dumps(person)

if __name__ == "__main__":
    app.run()
