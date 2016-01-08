import boto
from boto.s3.key import Key
import json
from prime.utils.crawlera import reformat_crawlera

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
conf = {"hbase.mapred.outputtable": "people",  
    "mapreduce.outputformat.class": "org.apache.hadoop.hbase.mapreduce.TableOutputFormat",  
    "mapreduce.job.output.key.class": "org.apache.hadoop.hbase.io.ImmutableBytesWritable",  
    "mapreduce.job.output.value.class": "org.apache.hadoop.io.Writable"}

def convert(line):
    linkedin_data = json.loads(line)
    linkedin_id = linkedin_data.get("linkedin_id")
    if linkedin_id:
        return [(linkedin_id, [linkedin_id,"linkedin","line",line])]
    return []
# def convert_xwalk(line):
#     linkedin_data = json.loads(line)
#     return (linkedin_data["url"], [linkedin_data["url"],"linkedin","linkedin_id",linkedin_data["linkedin_id"]])

datamap = data.flatMap(convert)
#15 seconds to write
datamap.saveAsNewAPIHadoopDataset(conf=conf,keyConverter=keyConv,valueConverter=valueConv)


#read in from hbase
keyConv = "org.apache.spark.examples.pythonconverters.ImmutableBytesWritableToStringConverter"
valueConv = "org.apache.spark.examples.pythonconverters.HBaseResultToStringConverter"
rdd = sc.newAPIHadoopRDD("org.apache.hadoop.hbase.mapreduce.TableInputFormat", "org.apache.hadoop.hbase.io.ImmutableBytesWritable", "org.apache.hadoop.hbase.client.Result", conf={"hbase.mapreduce.inputtable": "people"},keyConverter=keyConv,valueConverter=valueConv)
