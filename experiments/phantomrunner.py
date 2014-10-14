import subprocess
import tempfile
import os

import settings

class PhantomException(Exception):
    pass

def get_content(url):
    with open(os.devnull, 'wb') as fnull:
	with tempfile.NamedTemporaryFile() as f:
	    process = subprocess.call([
		'phantomjs', '{}/getcontent.js'.format(settings.PROJECT_ROOT), url, f.name
	    ], stdout=fnull, stderr=fnull)
	    

	    f.seek(0)
	    val = f.read()

	    if not val:
		raise PhantomException('Could not get value from phantomjs')
	    return val


