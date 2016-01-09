import boto
from boto.s3.key import Key
import json
from prime.utils.crawlera import reformat_crawlera
import happybase
AWS_KEY = "AKIAIZZBJ527CKPNY6YQ"
AWS_SECRET = "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"
AWS_BUCKET = "ac-crawlera"
S3_BUCKET = boto.connect_s3(AWS_KEY, AWS_SECRET).get_bucket(AWS_BUCKET)
PERIOD = "2015_12"
keys = S3_BUCKET.list("linkedin/people/" + PERIOD + "/")

keypaths = ["s3a://" + AWS_KEY + ":" + AWS_SECRET + "@" + AWS_BUCKET + "/" + key.name for key in keys]
filenames = ",".join(keypaths)
data = sc.textFile(filenames)

keyConv = "org.apache.spark.examples.pythonconverters.StringToImmutableBytesWritableConverter"
valueConv = "org.apache.spark.examples.pythonconverters.StringListToPutConverter"
conf = {"mapreduce.outputformat.class": "org.apache.hadoop.hbase.mapreduce.TableOutputFormat",  
    "mapreduce.job.output.key.class": "org.apache.hadoop.hbase.io.ImmutableBytesWritable",  
    "mapreduce.job.output.value.class": "org.apache.hadoop.io.Writable"}

def load_by_linkedin_id(line):
    linkedin_data = json.loads(line)
    linkedin_id = linkedin_data.get("linkedin_id")
    if linkedin_id:
                #key           #key again   #col.family   #col.name    #col.value
        return [(linkedin_id, [linkedin_id,"linkedin",   "line",       line])]
    return []

def load_xwalk(line):
    linkedin_data = json.loads(line)
    linkedin_id = linkedin_data.get("linkedin_id")
    url = linkedin_data.get("url")
    if not linkedin_id or not url:
        return []
             #key  #key again   #col.family   #col.name    #col.value
    return [(url, [url,         "linkedin_id","linkedin_id",linkedin_id])]

conf["hbase.mapred.outputtable"]="people"  
datamap = data.flatMap(load_by_linkedin_id)
#15 seconds to write. does not overwrite existing table; acts as an update
datamap.saveAsNewAPIHadoopDataset(conf=conf,keyConverter=keyConv,valueConverter=valueConv)

conf["hbase.mapred.outputtable"]="url_xwalk"  
datamap = data.flatMap(load_xwalk)
#36 minutes
datamap.saveAsNewAPIHadoopDataset(conf=conf,keyConverter=keyConv,valueConverter=valueConv)

connection = happybase.Connection('172.17.0.2')
xwalk = connection.table('url_xwalk')

def also_viewed(line):
    linkedin_data = json.loads(line)
    also_viewed = linkedin_data.get("also_viewed")
    linkedin_id = linkedin_data.get("linkedin_id")
    if not also_viewed or not linkedin_id:
        return []
    linkedin_ids = []
    for key, data in xwalk.rows(also_viewed):
        if data:
            linkedin_ids.append(data)        
    return [(linkedin_id, also_viewed)]

#read in from hbase - seems much slower than rdd loaded from S3
keyConv = "org.apache.spark.examples.pythonconverters.ImmutableBytesWritableToStringConverter"
valueConv = "org.apache.spark.examples.pythonconverters.HBaseResultToStringConverter"
rdd = sc.newAPIHadoopRDD("org.apache.hadoop.hbase.mapreduce.TableInputFormat", "org.apache.hadoop.hbase.io.ImmutableBytesWritable", "org.apache.hadoop.hbase.client.Result", conf={"hbase.mapreduce.inputtable": "people"},keyConverter=keyConv,valueConverter=valueConv)
