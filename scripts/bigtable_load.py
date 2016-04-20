import sys
import json

def output_company(line):
    linkedin_data = json.loads(line)
    unique_id = linkedin_data.get("_key")[2:]
    if unique_id:
        data_column = [(unique_id, [unique_id,"crawlera",   "linkedin_data",       line])]
                        #key   #key again   #col.family   #col.name    #col.value
        return data_column
    return []

def output_company_linkedin_id(line):
    linkedin_data = json.loads(line)
    unique_id = linkedin_data.get("_key")[2:]
    linkedin_id = linkedin_data.get("linkedin_id")
    if not unique_id or not linkedin_id:
        return []
    data_column = [(linkedin_id, [linkedin_id, "crawlera","unique_id",unique_id])]
    return data_column

def output_company_url(line):
    linkedin_data = json.loads(line)
    unique_id = linkedin_data.get("_key")[2:]
    url = linkedin_data.get("url")
    if not unique_id or not url:
        return []
    data_column = [(url, [url, "crawlera","unique_id",unique_id])]
    return data_column

def output_person(line):
    linkedin_data = json.loads(line)
    unique_id = linkedin_data.get("unique_id")
    if unique_id:
        data_column = [(unique_id, [unique_id,"crawlera",   "linkedin_data",       line])]
                        #key   #key again   #col.family   #col.name    #col.value
        return data_column
    return []

def output_linkedin_id(line):
    linkedin_data = json.loads(line)
    unique_id = linkedin_data.get("unique_id")
    linkedin_id = linkedin_data.get("linkedin_id")
    if not unique_id or not linkedin_id:
        return []
    data_column = [(linkedin_id, [linkedin_id, "crawlera","unique_id",unique_id])]
    return data_column

def output_url(line):
    linkedin_data = json.loads(line)
    unique_id = linkedin_data.get("unique_id")
    if not unique_id:
        return []    
    all_urls = []
    url = linkedin_data.get("url")
    if url not in all_urls:
        all_urls.append(url)    
    url = linkedin_data.get("canonical_url")
    if url and url not in all_urls:
        all_urls.append(url)  
    url = linkedin_data.get("redirect_url")
    if url and url not in all_urls:
        all_urls.append(url)        
    for url in linkedin_data.get("previous_urls",[]):
        if url and url not in all_urls:
            all_urls.append(url)          
    data = []
    for url in all_urls:
        data.append((url, [url, "crawlera","unique_id",unique_id]))
    return data

def output_name_headline(line):
    linkedin_data = json.loads(line)
    unique_id = linkedin_data.get("unique_id")
    full_name = linkedin_data.get("full_name")
    headline = linkedin_data.get("headline")
    if not unique_id or not full_name or not headline:
        return []
    rowkey = full_name + headline
    data_column = [(rowkey, [rowkey, "crawlera","unique_id",unique_id])]
    return data_column

#WE HAVE UP TO 200 VERSIONS FOR THE CELL IN THIS TABLE. THEREFORE EACH OUPUT DOESNT OVERWRITE. 
#WE SAVE OURSELVES FROM HAVING TO AGGREGATE OR GROUP BY KEY
#ALSO WITH EACH MONTH WE GET NEW URLS AND THE QUERY DOESNT HAVE TO CHANGE
def output_also_viewed_reverse(line):
    linkedin_data = json.loads(line)
    unique_id = linkedin_data.get("unique_id")
    if not unique_id:
        unique_id = linkedin_data.get("_key")[2:]
    also_viewed = linkedin_data.get("also_viewed",[])
    output = []
    for url in also_viewed:
        output.append((url, [url, "crawlera","unique_id",unique_id]))
    return output


class BigTableLoader(object):

    def __init__(self, period, _sc):
        self.sc = _sc
        self.PERIOD = period
        self.project = 'advisorconnect-1238'
        self.zone = 'us-central1-b'
        self.cluster = 'crawlera'
        self.data = self.sc.textFile("gs://crawlera-linkedin-profiles/linkedin/people/{}/*".format(self.PERIOD))
        self.company_data = self.sc.textFile("gs://crawlera-linkedin-profiles/linkedin/companies/{}/*".format(self.PERIOD))
        self.keyConv_read = "org.apache.spark.examples.pythonconverters.ImmutableBytesWritableToStringConverter"
        self.valueConv_read = "org.apache.spark.examples.pythonconverters.HBaseResultToStringConverter"                     
        self.keyConv_write = "org.apache.spark.examples.pythonconverters.StringToImmutableBytesWritableConverter"
        self.valueConv_write = "org.apache.spark.examples.pythonconverters.StringListToPutConverter"       
        self.table_input_format = "org.apache.hadoop.hbase.mapreduce.TableInputFormat"
        self.table_output_format = "org.apache.hadoop.hbase.mapreduce.TableOutputFormat"   
        self.table_output_class = "org.apache.hadoop.hbase.client.Result"  
        self.key_class = "org.apache.hadoop.hbase.io.ImmutableBytesWritable"   
        self.value_class = "org.apache.hadoop.io.Writable"
        self.conn_class = "com.google.cloud.bigtable.hbase1_1.BigtableConnection"
        self.conf = {"hbase.client.connection.impl": self.conn_class,
                    "google.bigtable.project.id": self.project,
                    "google.bigtable.zone.name": self.zone,
                    "google.bigtable.cluster.name": self.cluster,
                    "mapreduce.outputformat.class": self.table_output_format,  
                    "mapreduce.job.output.key.class": self.key_class,  
                     "mapreduce.job.output.value.class": self.value_class}

    def save(self, datamap, table_name):
        self.conf["hbase.mapred.outputtable"]=table_name
        #does not overwrite existing table; acts as an update -- 36 minutes
        datamap.saveAsNewAPIHadoopDataset(conf=self.conf,keyConverter=self.keyConv_write,
                                          valueConverter=self.valueConv_write)
    
    def load_companies(self):
        self.load_company_table()
        self.load_company_linkedin_ids()
        self.load_company_urls()
        
    def load_company_table(self):          
        datamap = self.company_data.flatMap(output_company)
        self.save(datamap, "company")

    def load_company_linkedin_ids(self):          
        datamap = self.company_data.flatMap(output_company_linkedin_id)
        self.save(datamap, "company_linkedin_ids")
   
    def load_company_urls(self):          
        datamap = self.company_data.flatMap(output_company_url)
        self.save(datamap, "company_urls")
        
    def load_people(self):
        self.load_people_table()
        self.load_linkedin_ids()
        self.load_urls()
        self.load_name_headline() #maybe dont let them query if the headline is --
        hb.load_also_viewed_reverse()
        
    def load_people_table(self):          
        datamap = self.data.flatMap(output_person)
        self.save(datamap, "people")
        
    def load_linkedin_ids(self):
        datamap = self.data.flatMap(output_linkedin_id)
        self.save(datamap, "linkedin_ids")
        
    def load_urls(self):
        datamap = self.data.flatMap(output_url)
        self.save(datamap, "urls")
        
    def load_name_headline(self):
        datamap = self.data.flatMap(output_name_headline)
        self.save(datamap, "name_headline")
        
    def load_also_viewed_reverse(self):
        datamap = self.data.flatMap(output_also_viewed_reverse)
        self.save(datamap, "also_viewed_reverse")
        
if __name__ == "__main__":
    period = sys.argv[1]
    hb = BigTableLoader(period,sc) 
    hb.load_people()

    # #one-time only
    # hb = BigTableLoader("2015-11",sc) 
    # hb.load_companies()



