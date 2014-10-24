import os

from flask import Flask, abort, Response

from url_db import UrlDB
from get_redis import get_redis

port = int(os.getenv('HEALTH_CHECK_PORT', '0'))
host = os.getenv('HEALTH_CHECK_HOST', '0.0.0.0')

app = Flask(__name__)
@app.route("/")
def health_check():
    url_db = UrlDB(get_redis())

    # return 200 if server is healthy
    if url_db.is_server_healthy():
        return Response('Ok', status=200)
    else:
        # and 500 if the server is uhealthy
        abort(500)

if __name__ == '__main__':
    app.run(port=port, host=host)
