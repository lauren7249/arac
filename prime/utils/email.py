from flask import current_app
import re
import requests
import boto
import os
import sendgrid

def sendgrid_email(to, subject, body, ccs=['lauren@advisorconnect.co','jimmy@advisorconnect.co','jeff@advisorconnect.co','jamesjohnson11@gmail.com']):
    sg = sendgrid.SendGridClient('lauren7249', '1250downllc')
    mail = sendgrid.Mail()
    mail.add_to(to)
    for cc in ccs:
        mail.add_cc(cc)
    mail.set_subject(subject)
    mail.set_html(body)
    mail.set_from('contacts@advisorconnect.co')
    status, msg = sg.send(mail)
    return status
