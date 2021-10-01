from .models import Folder, List, Story, Workspace
from django.forms import Form, CharField, EmailField, ChoiceField
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

class StoryForm(Form):
    name = CharField(max_length=32, required=True)
    desc = CharField(max_length=500, required=False)
    priority = ChoiceField(choices=Story.PriorityChoices.choices)
    status = ChoiceField(choices=Story.StatusChoices.choices)
    list_uuid = List
