import poplib
from email import parser
import uuid
from prime.prospects.models import PhoneExport, session
import sendgrid
import vobject

gmail_user = 'contacts@advisorconnect.co'
gmail_pwd = '1250downllc'
sg = sendgrid.SendGridClient('lauren7249',gmail_pwd)

while  True:
	pop_conn = poplib.POP3_SSL('pop.gmail.com')
	pop_conn.user(gmail_user)
	pop_conn.pass_(gmail_pwd)

	#Get messages from server:
	messages = [pop_conn.retr(i) for i in range(1, len(pop_conn.list()[1]) + 1)]
	messages = ["\n".join(mssg[1]) for mssg in messages]
	messages = [parser.Parser().parsestr(mssg) for mssg in messages]
	for message in messages:
		from_email = None
		data = None
		subject = None
		message_id = None
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
			mail.add_to('<' + from_email + '>')
			mail.set_subject(subject)
			mail.set_text(text)
			mail.set_from('<' + gmail_user + '>')
			status, msg = sg.send(mail)
	pop_conn.quit()