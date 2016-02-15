from flask.ext.wtf import Form
from wtforms import PasswordField, StringField
from wtforms.validators import InputRequired, Email
from prime.utils.linkedin_csv_getter import LinkedinCsvGetter

class LinkedinLoginForm(Form):
    email = StringField('Email', validators=[InputRequired(), Email()])
    password = PasswordField('Password', validators=[InputRequired()])

    def validate(self):
        if not Form.validate(self):
            return False
        #todo: remove
        #return True
        getter = LinkedinCsvGetter(self.email.data, self.password.data)
        if getter.check_linkedin_creds():
            return getter
        self.password.errors.append("Incorrect Linkedin Email/Password Combination")
        return None

