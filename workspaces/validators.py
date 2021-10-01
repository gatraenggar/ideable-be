from .models import Folder, Workspace
from django.db.models.fields import UUIDField
from django.forms import Form, CharField, EmailField
import sys

sys.path.append("..")
from users.models import User

class WorkspaceForm(Form):
    name = CharField(max_length=32)
    owner = User

class WorkspaceMemberForm(Form):
    email = EmailField(max_length=254)

class WorkspaceFolderForm(Form):
    name = CharField(max_length=32)
    workspace_uuid = Workspace

class WorkspaceListForm(Form):
    name = CharField(max_length=32)
    folder_uuid = Folder
