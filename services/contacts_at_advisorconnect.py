import poplib
from email import parser
import uuid
from prime.prospects.models import PhoneExport, session
import sendgrid

gmail_user = 'contacts@advisorconnect.co'
gmail_pwd = '1250downllc'

while True:
	pop_conn = poplib.POP3_SSL('pop.gmail.com')
	pop_conn.user(gmail_user)
	pop_conn.pass_(gmail_pwd)
	sg = sendgrid.SendGridClient('lauren7249',gmail_pwd)

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
			if name and name.find('MyContacts-')==0: 
				from_email = message['From']
				subject = message['Subject']
				message_id = message['Message-ID']
				data = part.get_payload(decode=True)
				break
		if from_email and data:
			id = str(uuid.uuid4().int)
			e = PhoneExport(id=id, data=data, sent_from=from_email)
			session.add(e)
			session.commit()		
			text = 'Your export code is ' + id
			message = sendgrid.Mail()
			message.add_to('<' + from_email + '>')
			message.set_subject(subject)
			message.set_text(text)
			message.set_from('<' + gmail_user + '>')
			status, msg = sg.send(message)
	pop_conn.quit()