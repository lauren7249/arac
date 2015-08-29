
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



if __name__ == "__main__":
    app.run()

