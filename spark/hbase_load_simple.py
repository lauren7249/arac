import boto, re
from boto.s3.key import Key
import happybase
from flatmappers import *
from foldbykey import *

class HBaseLoader(object):

    def __init__(self, period, sc):
        self.sc = sc
        self.AWS_KEY = "AKIAIZZBJ527CKPNY6YQ"
        self.AWS_SECRET = "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"
        self.AWS_BUCKET = "ac-crawlera"
        self.S3_BUCKET = boto.connect_s3(self.AWS_KEY, self.AWS_SECRET).get_bucket(self.AWS_BUCKET)
        self.PERIOD = period
        self.keys = self.S3_BUCKET.list("linkedin/people/" + self.PERIOD + "/")
        self.keypaths = ["s3a://" + self.AWS_KEY + ":" + self.AWS_SECRET + "@" + self.AWS_BUCKET + "/" + key.name for key in self.keys]
        self.filenames = ",".join(self.keypaths)
        self.data = self.sc.textFile(self.filenames)
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

    def load_people_table(self):          
        #does not overwrite existing table; acts as an update -- 36 minutes
        self.conf["hbase.mapred.outputtable"]="people"  
        datamap = self.data.flatMap(load_people)
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

        self.conf["hbase.mapred.outputtable"]="url_xwalk"  
        datamap = self.data.flatMap(load_url_xwalk)
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

        #one-time deal since linkeidn id is becoming obsolete
        self.conf["hbase.mapred.outputtable"]="linkedin_id_xwalk"  
        datamap = self.data.flatMap(load_linkedin_id_xwalk)
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

    #still in dev
    def load_extended(self):     
        self.conf["hbase.mapred.outputtable"]="people"  
        self.xwalk = self.get_xwalk_rdd()
        datamap = self.data.flatMap(map_also_viewed).leftOuterJoin(self.xwalk).flatMap(create_edges).foldByKey([],append).flatMap(load_graph)
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

    def load_by_name(self):     
        self.conf["hbase.mapred.outputtable"]="linkedin_names"  
        datamap = self.data.flatMap(parse_names).foldByKey(([],[]),name_fold).flatMap(load_names)
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

    # def load_by_dob(self):     
    #     self.conf["hbase.mapred.outputtable"]="linkedin_dob"  
    #     datamap = self.data.flatMap(get_dob).foldByKey([],append).flatMap(load_by_dob)
    #     datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,valueConverter=self.valueConv_write)

    # def get_xwalk_rdd(self):
    #     #read in from hbase - seems much slower than rdd loaded from S3
    #     rdd = self.sc.newAPIHadoopRDD(self.table_input_format, self.key_class, self.table_output_class, conf={"hbase.mapreduce.inputtable": "url_xwalk"},keyConverter=self.keyConv_read,valueConverter=self.valueConv_read)
    #     return rdd

if __name__=="__main__":
    hb = HBaseLoader("2015_12", sc) 
    hb.load_people_table()   
    connection = happybase.Connection('172.17.0.2')
    data_table = connection.table('people')      
    data_table.row('11207608')