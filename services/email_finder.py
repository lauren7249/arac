import requests
import json
import urlparse
import smtplib
import os
import sys
sys.path.append(sys.path[0].split("/services")[0])

try:
    import DNS
except:
    import dns as DNS

from email_perumutations import generate_email_perms
from prime.prospects.helper import BingSearch



class EmailFinder(object):

    def __init__(self, name, company, *args, **kwargs):
        self.first_name, self.last_name = name.split(" ")
        self.company = company
        self.full_contact_api_key = "65d32e9341994d11"
        self.full_contact_url = "https://api.fullcontact.com/v2/person.json"
        self.full_contact_params = {"apiKey": self.full_contact_api_key}

    def find_url(self):
        bing = BingSearch("{}".format(self.company))
        items = bing.search()
        for item in items:
            url = item.get("Url")
            if not "linkedin.com" in url:
                self.domain = item.get("Url")
                self.email_domain = urlparse.urlparse(item.get("Url")).netloc.replace("www.", "")
                print self.email_domain
                self.permutations = generate_email_perms(self.first_name,
                        self.last_name, self.email_domain)
                return True

    def find_fullcontact_information(self):
        return None
        """
        for email in self.permutations:
            self.full_contact_params['email'] = email
            r = requests.get(self.full_contact_url, params=self.full_contact_params)
            results = json.loads(r.text)
            import pdb
            pdb.set_trace()
        return None
        """

    def find_smtp_information(self):
        results = DNS.mxlookup(self.email_domain)
        from_email = "sam@gs.com"
        if len(results) > 0:
            result = results[0][1]
            server = smtplib.SMTP(result, 25)
            server.helo()
            server.mail(from_email, "")
            for permutation in self.permutations:
                print permutation
                try:
                    code, info = server.rcpt(permutation)
                    if code == 250:
                        return permutation
                except Exception, e:
                    print e
                    pass
        pass

    def find_whois_information(self):
        pass

    def find_email_from_site(self):
        pass

    def find_contact_information(self):
        url = self.find_url()
        email = self.find_fullcontact_information()
        if not email:
            email = self.find_smtp_information()
            if not email:
                email = self.find_whois_information()
                #if not email:
                #    email = self.find_email_from_site()
            if email:
                return email
        return None


if __name__ =='__main__':
    ef = EmailFinder(name="Nathan Bruker", company="Goldman Sachs")
    ef.find_contact_information()

