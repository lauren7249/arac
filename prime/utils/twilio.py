from twilio.rest import TwilioRestClient

class TwilioCall(object):

    def __init__(self):
        self.account_sid = "ACf1aac47dd8d52ebeed3edc3eec50b330"
        self.auth_token = "a6f096245799d1393f03e7da181b23b4"
        self.client = TwilioRestClient(account_sid, auth_token)
        self.from_number ="+16502851186"
        self.url="http://twimlets.com/holdmusic?Bucket=com.twilio.music.ambient"

    def call(self, number):
        call = self.client.calls.create(to=number, from_=self.from_number, url=self.url)
