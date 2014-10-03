import subprocess
import tempfile
import os

import settings

def get_content(url):
    with open(os.devnull, 'wb') as fnull:
	with tempfile.NamedTemporaryFile() as f:
	    process = subprocess.call([
		'phantomjs', 'getcontent.js', url, f.name
	    ], stdout=fnull, stderr=fnull)
	    
	    f.seek(0)
	    return f.read()


