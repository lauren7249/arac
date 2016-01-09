import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(BASE_DIR)
from prime import create_app

application = create_app(os.getenv('AC_CONFIG', 'beta'))
print os.getenv('AC_CONFIG', 'beta') 

if __name__ == "__main__":
    print "WORKING"
    application.debug=True
    application.run()
