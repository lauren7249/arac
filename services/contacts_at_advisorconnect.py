import poplib
from email import parser
import uuid
from prime.prospects.models import PhoneExport, session
import sendgrid
import vobject
import getpass, imaplib
import time
import email

gmail_user = 'contacts@advisorconnect.co'
gmail_pwd = '1250downllc'
sg = sendgrid.SendGridClient('lauren7249',gmail_pwd)

imapSession = imaplib.IMAP4_SSL('imap.gmail.com')
typ, accountDetails = imapSession.login(gmail_user, gmail_pwd)
while  True:
	imapSession.select('INBOX')
	typ, data = imapSession.search(None, 'ALL')
	for msgId in data[0].split():
		typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
		emailBody = messageParts[0][1]
		from_email = None
		data = None
		subject = None
		message_id = None
		message = email.message_from_string(emailBody)
		for part in message.walk():
			name = part.get_filename()
			if name and name.find('MyContacts-')==0 and name.find('.vcf')>-1: 
				from_email = message['From']
				subject = message['Subject']
				message_id = message['Message-ID']
				data = part.get_payload(decode=True)
				break
		if from_email and data:
			id = str(uuid.uuid4().int)
			vcard = vobject.readComponents(data)
			j = []
			for item in vcard:
				d = {}
				for child in item.getChildren():
					value = child.value
					if not isinstance(value,basestring): value = str(value)
					d.update({child.name: value.encode('utf-8')})
				j.append(d)
			e = PhoneExport(id=id, data=j, sent_from=from_email)
			session.add(e)
			session.commit()		
			text = 'Your export code is ' + id
			mail = sendgrid.Mail()
			mail.add_to(from_email)
			mail.set_subject(subject)
			mail.set_text(text)
			mail.set_from(gmail_user)
			status, msg = sg.send(mail)
		imapSession.store(int(msgId), '+FLAGS', '\\Deleted')
		imapSession.expunge()
