from flask.ext.wtf import Form
from wtforms import PasswordField, StringField
from wtforms.validators import InputRequired, Email
from prime.processing_service.helper import check_linkedin_creds

class LinkedinLoginForm(Form):

    password = PasswordField('Password', validators=[InputRequired()])

    def validate(self, email):
        if not Form.validate(self):
            return False
        #todo: remove
        #return True
        driver = check_linkedin_creds(email, self.password.data)
        if driver:
            return driver
        self.password.errors.append("Incorrect Linkedin Password")
        return None

