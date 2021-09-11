from django.forms import Form, CharField, EmailField
import re

class RegistrationField(Form):
    email = EmailField(max_length=254)
    password = CharField(min_length=8, max_length=20)
    first_name = CharField(min_length=1, max_length=20)
    last_name = CharField(max_length=20)

class RegistrationForm():
    def __init__(self, payload):
        self.payload = payload

    def is_valid(self):
        if not RegistrationField(self.payload).is_valid(): return False

        invalidChars = re.search(r"[^a-zA-Z ]|^ | $", self.payload["first_name"])
        if invalidChars != None: return False

        invalidChars = re.search(r"[^a-zA-Z ]|^ | $", self.payload["last_name"])
        if invalidChars != None: return False

        return True

class LoginForm(Form):
    email = EmailField(max_length=254)
    password = CharField(min_length=8, max_length=20)

class ResendEmailForm(Form):
    email = EmailField(max_length=254)
