from .models import TaskAssignee, Folder, List, Story, Task, Workspace, WorkspaceMember
from django.forms import Form, CharField, EmailField, ChoiceField
import sys

sys.path.append("..")
from users.models import User

class WorkspaceForm(Form):
    name = CharField(min_length=2, max_length=32)
    owner = User

class WorkspaceMemberForm(Form):
    email = EmailField(max_length=254)

class WorkspaceFolderForm(Form):
    name = CharField(max_length=32)
    workspace_uuid = Workspace

class WorkspaceListForm(Form):
    name = CharField(max_length=32)

class StoryForm(Form):
    name = CharField(min_length=1, max_length=80, required=True)
    desc = CharField(max_length=500, required=False)
    priority = ChoiceField(choices=Story.PriorityChoices.choices)
    status = ChoiceField(choices=Story.StatusChoices.choices)
    list_uuid = List

    def is_patch_valid(story_form):
        payload = story_form.data

        if "name" in payload:
            if len(payload["name"]) < 1 or len(payload["name"]) > 80:
                return False
        if "desc" in payload:
            if len(payload["desc"]) < 1 or len(payload["desc"]) > 500:
                return False
        if "priority" in payload:
            if payload["priority"] not in Story.PriorityChoices.values:
                return False
        if "status" in payload:
            if payload["status"] not in Story.StatusChoices.values:
                return False
        if "list_uuid" in payload:
            if not isinstance(payload["list_uuid"], List):
                return False

        return True

class TaskForm(Form):
    name = CharField(min_length=1, max_length=80, required=True)
    desc = CharField(max_length=500, required=False)
    priority = ChoiceField(choices=Task.PriorityChoices.choices)
    status = ChoiceField(choices=Task.StatusChoices.choices)
    story_uuid = Story

    def is_patch_valid(task_form):
        payload = task_form.data

        if "name" in payload:
            if len(payload["name"]) < 1 or len(payload["name"]) > 80:
                return False
        if "desc" in payload:
            if len(payload["desc"]) < 1 or len(payload["desc"]) > 500:
                return False
        if "priority" in payload:
            if payload["priority"] not in Task.PriorityChoices.values:
                return False
        if "status" in payload:
            if payload["status"] not in Task.StatusChoices.values:
                return False
        if "story_uuid" in payload:
            if not isinstance(payload["story_uuid"], Story):
                return False

        return True

class TaskAssigneeForm(Form):
    task_uuid = Task
    member_uuid = WorkspaceMember

class SubTaskForm(Form):
    name = CharField(min_length=1, max_length=50, required=True)
    task_uuid = Task
    assignee_uuid = TaskAssignee

    def is_patch_valid(subtask_form):
        payload = subtask_form.data

        if "name" in payload:
            if len(payload["name"]) < 1 or len(payload["name"]) > 50:
                return False
        if "is_done" in payload:
            if isinstance(payload["is_done"], bool) == False:
                return False
        if "assignee_uuid" in payload:
            if not isinstance(payload["assignee_uuid"], TaskAssignee) and payload["assignee_uuid"] != None:
                return False

        return True

