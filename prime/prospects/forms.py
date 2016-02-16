from flask.ext.wtf import Form
from wtforms import PasswordField, StringField
from wtforms.validators import InputRequired, Email

class LinkedinLoginForm(Form):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])

    def validate(self):
        if not Form.validate(self):
            return False
        return True

