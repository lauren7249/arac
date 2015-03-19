import mandrill
from flask import render_template

from prime.users.models import User

def send_daily_email():
    for user in User.query.all():
        email = render_template('emails/email.html', user=user)
        import pdb
        pdb.set_trace()
        print email
        message = {'from_email': 'jeff@advisorconnect.co',
         'from_name': 'Advisor Connect',
         'headers': {'Reply-To': 'jeff@advisorconnect.co'},
         'html': email,
         'important': True,
         'subject': 'Your Advisorconnect prospects are ready!',
         'text': 'Visit http://prime.advisorconnect.co to retrieve your prospects.',
         'to': [{'email': user.email,
                 'type': 'to'}]}
        try:
             #result = self.mandrill_client.messages.send(message=message)
             pass
        except:
             print 'A mandrill error occurred: %s - %s' % (e.__class__, e)
        return True
