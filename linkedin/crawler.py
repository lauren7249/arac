import requests
import time
import csv
import gevent
from gevent import monkey
monkey.patch_all()

from scraper import process_request



def gen_chunks(reader, chunksize=10):
    chunk = []
    for i, line in enumerate(reader):
        if (i % chunksize == 0 and i > 0):
            yield chunk
            del chunk[:]
        #hack to ignore first line
        if line[0] != "FORM_TAX_PRD":
            chunk.append(line)
    yield chunk

f = open("stdout.csv", "r")
for lines in gen_chunks(f.read().split(",")):
    jobs = [gevent.spawn(process_request, line.strip('"')) for line in lines]
    gevent.joinall(jobs, timeout=None)
    for job in jobs:
        print job.value['status'], job.value['url']
        file = open("/Users/jamesjohnson/Projects/arachnid/content/%s.html" % job.value['url'].replace("/", ""), "w+")
        file.write(job.value['content'])
        file.close()

    time.sleep(2)
