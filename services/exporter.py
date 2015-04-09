import requests
import sendgrid
import base64
import StringIO
import csv

import tempfile
import json
import urlparse
import smtplib
import os
import sys
sys.path.append(sys.path[0].split("/services")[0])

from email_finder import EmailFinder
from prime.prospects.models import db

def uu(str):
    if str:
        return str.encode("ascii", "ignore").decode("utf-8")
    return None

class Exporter(object):

    def __init__(self, prospects, to_email, *args, **kwargs):
        self.prospects = prospects
        self.to_email = to_email
        self.csvfile = StringIO.StringIO()
        self.csvwriter = csv.writer(self.csvfile, quoting=csv.QUOTE_ALL)
        self.headers = ["Name", "Current Title", "Current Company",
                "Current Industry", "Current Location", "Email"]

    def _write_headers(self):
        self.csvwriter.writerow(self.headers)

    def _build_writer(self):
        self._write_headers()
        for prospect in self.prospects:
            if prospect.current_job:
                try:
                    email_finder = EmailFinder(prospect.name,
                            prospect.current_job.company, prospect.linkedin_id)
                    email = email_finder.find_contact_information()
                except:
                    email = None
                current_company = prospect.current_job.company.name
                current_title = prospect.current_job.title
            else:
                email = None
                current_company = None
                current_title = None
            self.csvwriter.writerow(
                    [uu(prospect.name), uu(current_title), uu(current_company),
                        uu(prospect.industry_raw), uu(prospect.location_raw), uu(email)])
        return True

    def _send_email(self):
        """
        message = {'attachments': [{'content': base64.b64encode(self.csvfile.getvalue()),
                          'name': 'export.csv',
                          'type': 'application/octet-stream'}],
         'from_email': 'jeff@advisorconnect.co',
         'from_name': 'Advisor Connect',
         'headers': {'Reply-To': 'jeff@advisorconnect.co'},
         'html': '<p>Your Advisorconnect csv export</p>',
         'important': True,
         'subject': 'Your Advisorconnect Export',
         'text': 'Your Advisorconnect csv export',
         'to': [{'email': self.to_email,
                 'type': 'to'}]}
        result = self.mandrill_client.messages.send(message=message)
        """ 
        sg = sendgrid.SendGridClient("advisorconnect", "500advisordevshop")
        message = sendgrid.Mail()

        message.add_to(self.to_email)
        message.set_from("jeff@advisorconnect.co")
        message.set_subject("Your Advisorconnect Export")
        message.set_html("<p>Your Advisorconnect csv export</p>")
        message.add_attachment_stream("export.csv", self.csvfile.getvalue())

        sg.send(message)
        return True

    def export(self):
        results = self._build_writer()
        email_sent = self._send_email()
        print "Email Sent"

