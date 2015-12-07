import psycopg2
import psycopg2.extras
import web
import json
from prime.utils.crawlera import reformat_crawlera
from prime.processing_service.pipl_service import PiplRequest

web.config.debug = False
urls = (
    '/get_person_by_url', 'get_person_by_url'
)

CONNECTION_STRING = "dbname='ac_labs' user='arachnid' host='babel.priv.advisorconnect.co' password='devious8ob8'"
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
        query = """SELECT * from people where url in %s""" % (urls_string)
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
        query = """SELECT * from people where also_viewed @>'["%s"]'""" % (url)
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
            query = """SELECT * from people where url='%s'""" % (url)
        else:
            query = """SELECT * from people where linkedin_id='%s'""" % (linkedin_id)
        cur.execute(query)
        row = cur.fetchone()
        if not row:
            return {}
        row = dict(row)
        output = reformat_crawlera(row)
        return output
    return {}

def get_profile_by_any_url(url):
    profile = get_person(url=url)
    if profile:
        return profile
    request = PiplRequest(url, type="url", level="social")
    pipl_data = request.process()
    profile_linkedin_id = pipl_data.get("linkedin_id")
    profile = get_person(linkedin_id=profile_linkedin_id)
    return profile

def get_associated_profiles(linkedin_data):
    if not linkedin_data:
        return []
    source_url = linkedin_data.get("source_url")
    linkedin_id = linkedin_data.get("linkedin_id")
    if not source_url or not linkedin_id:
        return []
    also_viewed_urls = linkedin_data.get("urls",[])
    also_viewed = []
    for url in also_viewed_urls:
        profile = get_profile_by_any_url(url)
        if profile:
            also_viewed.append(profile)            
    viewed_also = get_people_viewed_also(url=source_url)
    if len(viewed_also) == 0:
        request = PiplRequest(linkedin_id, type="linkedin", level="social")
        pipl_data = request.process()
        new_url = pipl_data.get("linkedin_urls")
        viewed_also = get_people_viewed_also(url=new_url)
    return also_viewed + viewed_also

class get_person_by_url:
    def POST(self):
        d = json.loads(web.data())
        url = d.get("url","")
        version = d.get("api_version")
        person = get_profile_by_any_url(url)
        return json.dumps(person)

if __name__ == "__main__":
    app.run()
