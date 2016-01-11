import boto, re
from boto.s3.key import Key
import json
from prime.utils.crawlera import reformat_crawlera
from prime.processing_service.helper import name_match
import happybase
from operator import add

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

def map_also_viewed(line):
    linkedin_data = json.loads(line)
    also_viewed = linkedin_data.get("also_viewed")
    linkedin_id = linkedin_data.get("linkedin_id")
    name = linkedin_data.get("full_name")
    if not also_viewed or not linkedin_id or not name:
        return []
    urls = []    
    for url in also_viewed:
        _name = re.search('http://www.linkedin.com/[^/]+/[^/]+(?=/*)',url)
        if _name:
            _name = _name.group(0).split("/")[-1].replace("-"," ").lower()
            _name = re.sub('[^a-z\s]','',_name)
            if name_match(name, _name): continue         
        urls.append(url)
    #we already have the linkedin id of the current person, so expose the url of the other person as a key to merge with the xwalk and get a linkedin_id
    results =  [(url, linkedin_id) for url in urls]    
    return results

def create_edges(rec):
    #input will look  like (url2, (linkedin_id1, xwalk2))
    url2 = rec[0]
    linkedin_id1 = rec[1][0]
    xwalk2 = rec[1][1]
    linkedin_id2 = json.loads(xwalk2).get("value")
    #we couldnt find the url in the database, so just keep the url and we will handle it in load_graph
    if linkedin_id2 is None:
        linkedin_id2 = url2
    return [(linkedin_id1, linkedin_id2), (linkedin_id2, linkedin_id1)]

def load_graph(rec):
    linkedin_id = rec[0]
    arr = rec[1]
    urls = [e for e in arr if not e.isdigit()]
    linkedin_ids = [e for e in arr if e.isdigit()]
    return [(linkedin_id, [linkedin_id,"extended","urls",urls]), (linkedin_id, [linkedin_id,"extended","linkedin_ids",linkedin_ids])]

def append(a, b):
    return a.append(b)

class HBaseLoader(object):

    def __init__(self, period):
        self.AWS_KEY = "AKIAIZZBJ527CKPNY6YQ"
        self.AWS_SECRET = "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"
        self.AWS_BUCKET = "ac-crawlera"
        self.S3_BUCKET = boto.connect_s3(self.AWS_KEY, self.AWS_SECRET).get_bucket(self.AWS_BUCKET)
        self.PERIOD = period
        self.keys = self.S3_BUCKET.list("linkedin/people/" + self.PERIOD + "/")
        self.keypaths = ["s3a://" + self.AWS_KEY + ":" + self.AWS_SECRET + "@" + self.AWS_BUCKET + "/" + key.name for key in self.keys]
        self.filenames = ",".join(self.keypaths)
        self.data = sc.textFile(self.filenames)
        self.conf = {"mapreduce.outputformat.class": "org.apache.hadoop.hbase.mapreduce.TableOutputFormat",  
                    "mapreduce.job.output.key.class": "org.apache.hadoop.hbase.io.ImmutableBytesWritable",  
                     "mapreduce.job.output.value.class": "org.apache.hadoop.io.Writable"}

    def load_people_table(self):
        self.keyConv = "org.apache.spark.examples.pythonconverters.StringToImmutableBytesWritableConverter"
        self.valueConv = "org.apache.spark.examples.pythonconverters.StringListToPutConverter"            
        self.conf["hbase.mapred.outputtable"]="people"  
        datamap = self.data.flatMap(load_by_linkedin_id)
        #15 seconds to write. does not overwrite existing table; acts as an update
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv,valueConverter=self.valueConv)
        self.conf["hbase.mapred.outputtable"]="url_xwalk"  
        datamap = self.data.flatMap(load_xwalk)
        #36 minutes
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv,valueConverter=self.valueConv)

    def load_extended(self):
        self.keyConv = "org.apache.spark.examples.pythonconverters.StringToImmutableBytesWritableConverter"
        self.valueConv = "org.apache.spark.examples.pythonconverters.StringListToPutConverter"            
        self.conf["hbase.mapred.outputtable"]="people"  
        self.xwalk = self.get_xwalk_rdd()
        datamap = self.data.flatMap(map_also_viewed).leftOuterJoin(self.xwalk).flatMap(create_edges).foldByKey([],append).flatMap(load_graph)
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv,valueConverter=self.valueConv)
        return datamap

    def get_people_rdd(self):
        #read in from hbase - seems much slower than rdd loaded from S3
        self.keyConv = "org.apache.spark.examples.pythonconverters.ImmutableBytesWritableToStringConverter"
        self.valueConv = "org.apache.spark.examples.pythonconverters.HBaseResultToStringConverter"
        rdd = sc.newAPIHadoopRDD("org.apache.hadoop.hbase.mapreduce.TableInputFormat", "org.apache.hadoop.hbase.io.ImmutableBytesWritable", "org.apache.hadoop.hbase.client.Result", conf={"hbase.mapreduce.inputtable": "people"},keyConverter=self.keyConv,valueConverter=self.valueConv)
        return rdd

    def get_xwalk_rdd(self):
        #read in from hbase - seems much slower than rdd loaded from S3
        self.keyConv = "org.apache.spark.examples.pythonconverters.ImmutableBytesWritableToStringConverter"
        self.valueConv = "org.apache.spark.examples.pythonconverters.HBaseResultToStringConverter"
        rdd = sc.newAPIHadoopRDD("org.apache.hadoop.hbase.mapreduce.TableInputFormat", "org.apache.hadoop.hbase.io.ImmutableBytesWritable", "org.apache.hadoop.hbase.client.Result", conf={"hbase.mapreduce.inputtable": "url_xwalk"},keyConverter=self.keyConv,valueConverter=self.valueConv)
        return rdd