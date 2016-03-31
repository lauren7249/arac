
from prime.users.models import *
from helpers.stringhelpers import uu
import csv

csvfile = open("exclusions.csv","wb")
writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
all_users = User.query.all()
for user in all_users:
    data = user.exclusions_report
    if not data:
        continue
    for rownum in xrange(1, len(data)):
        row = data[rownum]
        if row[1] not in ['Not found in LinkedIn']:
            continue
        writer.writerow(row)
        # for colnum in xrange(0, len(row)):
        #     col = row[colnum]
        #     try:
        #         worksheet.write(rownum, colnum, uu(col))
        #     except:
        #         worksheet.write(rownum, colnum, uu(str(col)))
        # f.write("\r\n")
csvfile.close()

import tinys3      
from prime.processing_service.constants import AWS_KEY, AWS_SECRET, AWS_BUCKET
conn = tinys3.Connection(AWS_KEY, AWS_SECRET, AWS_BUCKET, tls=True)
f = open('exclusions.csv','rb')
conn.upload('exclusions.csv',f,'li-cookies')