import subprocess
import tempfile
import os

import settings

GET_CONTENT_PATH = os.path.realpath(__file__).split(os.path.sep)[:-1].join(os.path.sep)

class PhantomException(Exception):
    pass

def get_content(url):
    with open(os.devnull, 'wb') as fnull:
        with tempfile.NamedTemporaryFile() as f:
            process = subprocess.call([
            'phantomjs', GET_CONTENT_PATH, url, f.name
        ], stdout=fnull, stderr=fnull)

        f.seek(0)
        val = f.read()

        if not val:
            raise PhantomException('Could not get value from phantomjs')

        return val


