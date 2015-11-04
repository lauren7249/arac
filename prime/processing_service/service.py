import hashlib
import logging
import requests
import boto
from dateutil.parser import parser

from boto.s3.key import Key

from constants import AWS_KEY, AWS_SECRET, AWS_BUCKET, GLOBAL_HEADERS

class Service(object):

    def __init__(self):
        pass

    def _validate_data(self):
        return False

    def _get_current_job_from_cloudsponge(self, person):
        for csv_person in self.data:
            for email in csv_person.get("email"):
                person_email = person.get("email", [{}])[0].get("address")
                if email.get("email", {}).get("address") == person_email:
                    if email.get("company"):
                        job["company"] = email.get("company")
                    if email.get("title"):
                        job["title"] = email.get("job_title")
                    return job
        return {}


    def _get_current_job_from_experiences(self, person):
        """
        Helper method useful on several child services
        """
        if len(person.get("linkedin_data").get("experiences")) > 0:
            jobs = person.get("linkedin_data").get("experiences")
            current_job =filter(lambda x:x.get("end_date") == "Present", jobs)
            if len(current_job) == 1:
                return current_job[0]
            present_jobs = [job for job in jobs if job.get("end_date") is None]
            if len(present_jobs):
                start_date_jobs = [job for job in present_jobs if job.get("start_date")]
            else:
                start_date_jobs = [job for job in jobs if job.get("start_date")]
            if len(start_date_jobs) == 0:
                return jobs[0]
            return sorted(start_date_jobs, key=lambda x:x.start_date, reverse=True)[0]
        return {}

    def _current_job(self, person):
        job = {}
        current_job = self._get_current_job_from_experiences(person)
        if current_job.get("end_date") == "Present":
            return current_job
        end_date = parser.parse(current_job.get("end_date")) if \
        current_job.get("end_date") else None
        if not end_date or end_date >= datetime.date.today():
            return current_job
        current_job = self._get_current_job_from_cloudsponge(self, person)
        if current_job:
            return current_job
        if person.get("linkedin_data").get("headline"):
            headline = person.get("linkedin_data").get("headline")
            if headline.find(" at "):
                job["title"] = headline.split(" at ")[0]
                job["company"] = " at ".join(headline.split(" at ")[1:])
            else:
                job["title"] = headline
            return job
        return None







    def process(self):
        pass

    def dispatch(self):
        pass

class TemporaryProspect(object):
    pass

class S3SavedRequest(object):

    """
    Instead of just making a request, this saves the exact request to s3 so we
    don't need to make it again
    """

    def __init__(self, *args, **kwargs):
        self.url = None
        self.headers = GLOBAL_HEADERS
        self.key = None

    @property
    def _s3_connection(self):
        s3conn = boto.connect_s3("AKIAIKCNCKG6RXJHWNFA", "GAwQwgy67hmp0lMShAV4O15zfDAfc8aKUoY7l2UC")
        return s3conn.get_bucket("aconn")

    def _make_request(self):
        self.key = hashlib.md5(self.url).hexdigest()
        key = Key(self._s3_connection)
        key.key = self.key
        if key.exists():
            html = key.get_contents_as_string()
        else:
            response = requests.get(self.url, headers=self.headers)
            html = response.content
            key.content_type = 'text/html'
            key.set_contents_from_string(html)
        return html
