
import web
from cloudsponge import CloudSponge
web.config.debug = False
urls = (
    '/get_url/service=(.+)', 'get_url',
)

app = web.application(urls, globals())
web_session = web.session.Session(app, web.session.DiskStore('sessions'), initializer={'count': 0})

client = CloudSponge('VB652MMUEG24H4JF3SGL','GSrAxStb9Zk5EOmD')
class get_url:
    def GET(self, service):
        resp = client.begin_import(service)
        return { "url": resp['url'], "import_id":resp['import_id']}

if __name__ == "__main__":
    app.run()

