import psycopg2
import psycopg2.extras
import web
import json

web.config.debug = False
urls = (
    '/get_person_by_url', 'get_person_by_url'
)

app = web.application(urls, globals())
web_session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})

def get_person(url=None, version='1.0.0'):
    if not url:
        return None
    try:
        conn = psycopg2.connect("dbname='ac_labs' user='arachnid' host='babel.priv.advisorconnect.co' password='devious8ob8'")
    except:
        print "unable to connect to the database"
        return {}
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    if version=='1.0.0':
        from prime.utils.crawlera import reformat_crawlera
        query = """SELECT * from people where url='%s'""" % (url)
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
        url = d.get("url","").replace("https://","http://")
        version = d.get("api_version")
        person = get_person(url=url, version=version)
        return json.dumps(person)

if __name__ == "__main__":
    app.run()
