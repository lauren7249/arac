#mv  "/Users/lauren/Downloads/SUMALL client test 10.26.2015 - mj_2.csv.csv" ~/sumall.csv
#scp ~/sumall.csv moscow.priv.advisorconnect.co:~/arachnid/
import pandas
import re
import json
import multiprocessing
from random import shuffle

from prime.processing_service.clearbit_service import ClearbitService
from prime.processing_service.constants import pub_profile_re

df = pandas.read_csv("sumall.csv")
emails = df.email.values.tolist()

shuffle(emails)

emails_json = []

for email in emails:
    rec = {email: {}}
    emails_json.append(rec)

service = ClearbitService(None, None, emails_json)

data = service.process()

n_urls = 0
n_pub = 0
for record in data:
    url = record[record.keys()[0]].get("linkedin_urls")
    if not url:
        continue
    n_urls+=1
    linkedin_url = url
    if re.search(pub_profile_re,linkedin_url):
        n_pub+=1
    else:
        try:
            print linkedin_url
        except:
            pass
#34 urls
#30 pub
print n_urls
print n_pub

s = unicode(json.dumps(data, ensure_ascii=False))
f = open("leads.json", "w")
f.write(s.encode('utf8', 'replace'))
f.close()

# f = open("leads.json", "r")
# s = f.read()
# data = json.loads(s.decode("utf-8-sig"))
