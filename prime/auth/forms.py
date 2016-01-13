from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, HiddenField
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
    password = PasswordField('New Password', validators=[InputRequired(),
                                                         EqualTo('password2', message='Passwords must match'),
                                                         Length(min=8,
                                                                message='Passwords must be at least 8 characters long.')])
    password2 = PasswordField('Confirm password', validators=[InputRequired()])

    code = HiddenField("code")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
        return True

class ForgotForm(Form):
    email = StringField('Email', validators=[InputRequired(), Email()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
        return True
