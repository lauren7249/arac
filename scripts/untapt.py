
from prime.processing_service.person_request import PersonRequest
from prime.processing_service.age_service import AgeRequest
from prime.processing_service.gender_service import GenderRequest
from prime.processing_service.helper import get_firstname
from prime.utils.crawlera import reformat_crawlera
from prime.processing_service.pipl_request import PiplRequest
from prime.processing_service.geocode_service import GeocodeRequest, GeoPoint
import boto
from boto.s3.key import Key
import json
import datetime
import numpy
from random import shuffle

AWS_KEY = "AKIAIZZBJ527CKPNY6YQ"
AWS_SECRET = "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"
AWS_BUCKET = "ac-crawlera"
S3_BUCKET = boto.connect_s3(AWS_KEY, AWS_SECRET).get_bucket(AWS_BUCKET)
PERIOD = "2015_12"
keys = S3_BUCKET.list("linkedin/people/" + PERIOD + "/")

keypaths = ["s3a://" + AWS_KEY + ":" + AWS_SECRET + "@" + AWS_BUCKET + "/" + key.name for key in keys]
filenames = ",".join(keypaths[:1])
data = sc.textFile(filenames)
filenames = ",".join(keypaths)
fulldata = sc.textFile(filenames)

nyc = GeoPoint(40.7557, -73.99338)
sanfran = GeoPoint(37.80893, -122.26469)

def in_area(coords):
    if not coords:
        return False
    latlng = coords.get("latlng")
    geopoint = GeoPoint(latlng[0],latlng[1])
    locality = coords.get("locality").split(",")[-1].strip() if coords.get("locality") else ""
    region = coords.get("region").split(",")[-1].strip() if coords.get("region") else ""
    if region in ["Tennessee","Kansas","Texas"] or locality in ["Tennessee","Kansas","Texas"]:
        return True
    if geopoint.distance_to(sanfran)<=200:
        return True
    if geopoint.distance_to(nyc)<=120:
        return True
    return False

def in_set(line):
    try:
        linkedin_data = json.loads(line)
        linkedin_data = reformat_crawlera(linkedin_data)
    except Exception, e:
        print e
        return []    
    linkedin_id = linkedin_data.get("linkedin_id")
    if not linkedin_id:    
        return []         
    pr = PersonRequest()
    technical_degree = pr.has_technical_degree(linkedin_data)
    if not technical_degree:
        return []    
    programmer_points = pr.programmer_points(linkedin_data)
    if programmer_points<4:
        return []    
    dob_year_range = AgeRequest()._get_dob_year_range(linkedin_data)
    if not max(dob_year_range): 
        return []     
    min_age = datetime.datetime.today().year - max(dob_year_range)
    if min_age>35:
        return []    
    max_age = datetime.datetime.today().year - min(dob_year_range)
    if max_age<22:
        return []     
    firstname = get_firstname(linkedin_data.get("full_name"))
    is_male = GenderRequest(firstname).process()
    if is_male!=False:
        return []  
    location_raw = linkedin_data.get("location")
    coords = GeocodeRequest(location_raw).process()        
    if not in_area(coords):
        return []
    return [(linkedin_id, technical_degree.get("degree"), pr._current_job_linkedin(linkedin_data).get("title"), numpy.mean([min_age,max_age]), firstname, coords.get("locality"), coords.get("region"))]

def get_emails(rec):
    linkedin_id = rec[0]
    emails = PiplRequest(linkedin_id, level='email',type='linkedin').get_emails()
    return emails

inset = fulldata.flatMap(in_set)
inset.cache()
emails = inset.flatMap(get_emails)
emails.cache()
#inset.saveAsTextFile("s3a://" + AWS_KEY + ":" + AWS_SECRET + "@advisorconnect-bigfiles/untapt/matchesv1")

OUT_BUCKET = boto.connect_s3(AWS_KEY, AWS_SECRET).get_bucket("advisorconnect-bigfiles")
em = emails.take(20000)
key = Key(OUT_BUCKET)
key.key = 'untapt/emailsv1.txt'
key.content_type = "text/plain"
key.set_contents_from_string("\n".join(em))
count = 0
for rec in em:
    if rec.find("@gmail.com")>-1:
        print rec
        count+=1
        if count>=1000: break

s = inset.take(30000)
key = Key(OUT_BUCKET)
key.key = 'untapt/matchesv1.txt'
key.content_type = "text/json"
key.set_contents_from_string(str(s))

