from flask import current_app
import re
import requests
import boto
import os
import sendgrid

def sendgrid_email(to, subject, body):
    sg = sendgrid.SendGridClient(current_app.config.get("SENDGRID_EMAIL"),
            current_app.config.get("SENDGRID_PASSWORD"))

    mail = sendgrid.Mail()
    mail.add_to(to)
    mail.set_subject(subject)
    mail.set_html(body)
    mail.set_from(current_app.config.get("SENDGRID_FROM_EMAIL"))
    status, msg = sg.send(mail)
    return status
