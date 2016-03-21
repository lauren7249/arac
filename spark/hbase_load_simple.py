import boto, re
from boto.s3.key import Key
import happybase
import gzip
import StringIO
from flatmappers import *
from foldbykey import *

class HBaseLoader(object):

    def __init__(self, period, sc):
        self.sc = sc
        self.AWS_KEY = "AKIAIZZBJ527CKPNY6YQ"
        self.AWS_SECRET = "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"
        self.AWS_BUCKET = "ac-crawlera"
        self.AWS_BUCKET_ZIPPED = "crawlera-linkedin-profiles"
        self.S3_BUCKET = boto.connect_s3(self.AWS_KEY, self.AWS_SECRET).get_bucket(self.AWS_BUCKET_ZIPPED)
        self.S3_BUCKET_ZIPPED = boto.connect_s3(self.AWS_KEY, self.AWS_SECRET).get_bucket(self.AWS_BUCKET_ZIPPED)
        self.PERIOD = period
        self.keyConv_read = "org.apache.spark.examples.pythonconverters.ImmutableBytesWritableToStringConverter"
        self.valueConv_read = "org.apache.spark.examples.pythonconverters.HBaseResultToStringConverter"                     
        self.keyConv_write = "org.apache.spark.examples.pythonconverters.StringToImmutableBytesWritableConverter"
        self.valueConv_write = "org.apache.spark.examples.pythonconverters.StringListToPutConverter"       
        self.table_input_format = "org.apache.hadoop.hbase.mapreduce.TableInputFormat"
        self.table_output_format = "org.apache.hadoop.hbase.mapreduce.TableOutputFormat"   
        self.table_output_class = "org.apache.hadoop.hbase.client.Result"  
        self.key_class = "org.apache.hadoop.hbase.io.ImmutableBytesWritable"   
        self.value_class = "org.apache.hadoop.io.Writable"
        self.conf = {"mapreduce.outputformat.class": self.table_output_format,  
                    "mapreduce.job.output.key.class": self.key_class,  
                     "mapreduce.job.output.value.class": self.value_class}

    def get_s3_data(self):
        self.keys = self.S3_BUCKET.list("linkedin/people/" + self.PERIOD + "/")
        self.keypaths = ["s3a://" + self.AWS_KEY + ":" + self.AWS_SECRET + "@" + self.AWS_BUCKET_ZIPPED + "/" + key.name for key in self.keys]
        self.filenames = ",".join(self.keypaths)
        self.data = self.sc.textFile(self.filenames)
        return self.data

    def load_url_xwalk(self):
        self.conf["hbase.mapred.outputtable"]="url_xwalk"  
        datamap = self.data.flatMap(load_url_xwalk)
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

    #30 minutes?
    def load_people_table(self):          
        #does not overwrite existing table; acts as an update -- 36 minutes
        self.conf["hbase.mapred.outputtable"]="people"  
        datamap = self.data.flatMap(load_people)
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

    def load_linkedin_id_xwalk(self):
        self.conf["hbase.mapred.outputtable"]="linkedin_id_xwalk"  
        datamap = self.data.flatMap(load_linkedin_id_xwalk)
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)        

    # #still in dev -- probably will just use sql functionality
    # def load_extended(self):     
    #     self.conf["hbase.mapred.outputtable"]="people"  
    #     self.xwalk = self.get_xwalk_rdd()
    #     datamap = self.data.flatMap(map_also_viewed).leftOuterJoin(self.xwalk).flatMap(create_edges).foldByKey([],append).flatMap(load_graph)
    #     datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)
        #didnt work because the values were too big
    # def load_by_name(self):     
    #     self.conf["hbase.mapred.outputtable"]="linkedin_names"  
    #     datamap = self.data.flatMap(parse_names).foldByKey(([],[]),name_fold).flatMap(load_by_name)
    #     datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

    # def load_by_dob(self):     
    #     self.conf["hbase.mapred.outputtable"]="linkedin_dob"  
    #     datamap = self.data.flatMap(get_dob).foldByKey(([],[],[]),dob_fold).flatMap(load_by_dob)
    #     datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

    # def load_by_zip(self):     
    #     self.conf["hbase.mapred.outputtable"]="linkedin_zip"  
    #     datamap = self.data.flatMap(get_location).foldByKey([],append).flatMap(geocode).flatMap(load_by_zip)
    #     datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

    # def get_xwalk_rdd(self):
    #     #read in from hbase - seems much slower than rdd loaded from S3
    #     rdd = self.sc.newAPIHadoopRDD(self.table_input_format, self.key_class, self.table_output_class, conf={"hbase.mapreduce.inputtable": "url_xwalk"},keyConverter=self.keyConv_read,valueConverter=self.valueConv_read)
    #     return rdd

if __name__=="__main__":
    hb = HBaseLoader("2015_12", sc) 
    hb.load_people_table()   
    hb.get_s3_data()
    connection = happybase.Connection('172.17.0.2')
    data_table = connection.table('people')      
    data_table.row('11207608')