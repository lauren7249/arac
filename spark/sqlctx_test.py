from pyspark.sql.functions import array_contains
from helpers.linkedin_helpers import get_dob_year_range
from prime.utils.crawlera import reformat_crawlera
#test function

class PeopleFetcher(object):

    def __init__(self, period, sc, sqlCtx):
        self.sc = sc
        self.AWS_KEY = "AKIAIZZBJ527CKPNY6YQ"
        self.AWS_SECRET = "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"
        self.AWS_BUCKET = "ac-crawlera"
        self.S3_BUCKET = boto.connect_s3(self.AWS_KEY, self.AWS_SECRET).get_bucket(self.AWS_BUCKET)
        self.PERIOD = period
        self.keys = self.S3_BUCKET.list("linkedin/people/" + self.PERIOD + "/")
        self.keypaths = ["s3a://" + self.AWS_KEY + ":" + self.AWS_SECRET + "@" + self.AWS_BUCKET + "/" + key.name for key in self.keys]
        self.filenames = ",".join(self.keypaths)
        self.people_rdd = self.sc.jsonFile(self.filenames)
        self.people_rdd.registerTempTable("people")
        self.sqlCtx.registerFunction("get_dob_year_range",get_dob_year_range)
        self.people_dataFrame = self.sqlCtx.sql("""select *, get_dob_year_range(education, experience) as dob_year_range, dob_year_range[0] as dob_year_min, dob_year_range[1] as dob_year_max from people """)

        def get_viewed_also(self, url):
            also_viewed = self.people_dataFrame.where(array_contains(self.people_dataFrame.also_viewed,url)==True)
            return also_viewed.collect()