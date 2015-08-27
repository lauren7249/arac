
import web, json
from web.wsgiserver import CherryPyWSGIServer
from prime.prospects.get_prospect import session
from prime.prospects.models import CloudspongeRecord
# CherryPyWSGIServer.ssl_certificate = "server.crt"
# CherryPyWSGIServer.ssl_private_key = "server.key"
web.config.debug = False
urls = (
    '/add', 'add',
)

app = web.application(urls, globals())

class add:
    def POST(self):
		web.header('Access-Control-Allow-Origin', '*')
		web.header('Access-Control-Allow-Credentials', 'true')    	
		web.header('Access-Control-Allow-Headers', '*')
		web.header('Access-Control-Allow-Methods','*')
		i = web.data()
		for record in json.loads(i):
			owner = record.get("contacts_owner",{})
			contact = record.get("contact",{})
			r = CloudspongeRecord(owner=owner, contact=contact)
			session.add(r)
		session.commit()

if __name__ == "__main__":
    app.run()

