from pyspark.sql.functions import array_contains
from helpers.linkedin_helpers import get_dob_year_range
import happybase
from prime.utils.crawlera import reformat_schools, reformat_jobs
class PeopleFetcher(object):

    def __init__(self, period, sc, sqlCtx, obs=None, file_pattern='.jl'):
        self.sc = sc
        self.sqlCtx = sqlCtx
        self.AWS_KEY = "AKIAIZZBJ527CKPNY6YQ"
        self.AWS_SECRET = "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"
        self.sc._jsc.hadoopConfiguration().set("fs.s3n.awsAccessKeyId",self.AWS_KEY)
        self.sc._jsc.hadoopConfiguration().set("fs.s3n.awsSecretAccessKey", self.AWS_SECRET)
        self.AWS_BUCKET = "ac-crawlera"
        self.PERIOD = period
        self.people_rdd = self.sqlCtx.read.json("s3n://" + self.AWS_BUCKET + "/linkedin/people/" + self.PERIOD + "/*" + file_pattern)
        self.people_rdd.registerTempTable("people")
        self.sqlCtx.registerFunction("get_dob_year_range",lambda (education, experience): get_dob_year_range(reformat_schools(education), reformat_jobs(experience)))
        # self.people_dataFrame = self.sqlCtx.sql("""select *, get_dob_year_range(education, experience) as dob_year_range, dob_year_range[0] as dob_year_min, dob_year_range[1] as dob_year_max from people """).drop("dob_year_range")
        # if obs:
        #     self.people_dataFrame = self.people_dataFrame.limit(obs)
        # self.people_dataFrame.cache()

        def get_people_viewed_also(self, url):
            also_viewed = self.people_dataFrame.where(array_contains(self.people_dataFrame.also_viewed,url)==True)
            return also_viewed.collect()

        #def get_person(self, linkedin_id=None, url=None):

        # def query(self, name, dob_year):

if __name__=="__main__":
    fetcher = PeopleFetcher("2015_12", sc, sqlCtx, obs=1000)