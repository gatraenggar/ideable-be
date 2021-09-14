from django.forms import Form, CharField, EmailField
import sys

sys.path.append("..")
from users.models import User

class WorkspaceForm(Form):
    name = CharField(max_length=32)
    owner = User

class WorkspaceMemberForm(Form):
    email = EmailField(max_length=254)
