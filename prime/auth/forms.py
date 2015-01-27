from flask.ext.wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import Length, Email, InputRequired, EqualTo

from prime.users.models import User

class LoginForm(Form):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])

    def validate(self):
        if not Form.validate(self):
            return False
        user = User.query.filter_by(email = self.email.data.lower()).first()
        if user:
            if not user.check_password(self.password.data):
                self.password.errors.append("Incorrect Password")
                return False
            return True
        else:
            self.email.errors.append("That email is incorrect")
            return False


class SignUpForm(Form):
    first_name = StringField('First Name', validators=[InputRequired()])
    last_name = StringField('Last Name', validators=[InputRequired()])
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('New Password', validators=[InputRequired(),
                                                         EqualTo('password2', message='Passwords must match'),
                                                         Length(min=8,
                                                                message='Passwords must be at least 8 characters long.')])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
        user = User.query.filter_by(email = self.email.data.lower()).first()
        if user:
            self.email.errors.append("That email is already taken")
            return False
        else:
            return True
