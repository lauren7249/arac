from flask import current_app
import re
import requests
import boto
import os
import sendgrid

def sendgrid_email(to, subject, body, cc=None):
    sg = sendgrid.SendGridClient('lauren7249', '1250downllc')

    mail = sendgrid.Mail()
    mail.add_to(to)
    if cc:
        mail.add_cc(cc)
    mail.set_subject(subject)
    mail.set_html(body)
    mail.set_from('contacts@advisorconnect.co')
    status, msg = sg.send(mail)
    return status
