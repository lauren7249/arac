import logging
from service import Service
from constants import EXCLUDED_EMAIL_WORDS

class CloudSpongeService(Service):

    """
    Expected input is JSON of cloudsponge records
    """

    def __init__(self, user_email, user_linkedin_url, data, *args, **kwargs):
        self.user_email = user_email
        self.user_linkedin_url = user_linkedin_url
        self.data = data
        self.excluded_words = EXCLUDED_EMAIL_WORDS
        self.unique_emails = {}
        logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def dispatch(self):
        pass

    def process(self):
        self.logger.info('Starting Process: %s', 'Cloud Sponge Service')
        for person in self.data:
            #TODO save source also, where the email came from
            #eg {"sources": ["jlyons1004@gmail.com", "linkedin"]
            for email in person.get("email", []):
                email_address = email.get("address").lower()
                if not any(email_address in e for e in self.excluded_words):
                    job_title = person.get("job_title")
                    companies = person.get("companies")
                    self.unique_emails[email_address] = {"job_title": job_title,
                                                "companies": companies}
        self.logger.info('Emails Found: %s', len(self.unique_emails))
        self.logger.info('Ending Process: %s', 'Cloud Sponge Service')
        return self.unique_emails
