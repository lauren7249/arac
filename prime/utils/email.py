import sendgrid

def sendgrid_email(to, subject, body, ccs=['lauren@advisorconnect.co','jamesjohnson11@gmail.com'], from_email='support@advisorconnect.co'):
    sg = sendgrid.SendGridClient('lauren7249', '1250downllc')
    mail = sendgrid.Mail()
    mail.add_to(to)
    if ccs:
        for cc in ccs:
            mail.add_bcc(cc)
    mail.set_subject(subject)
    mail.set_html(body)
    mail.set_from(from_email)
    status, msg = sg.send(mail)
    return status
