from django.core.checks.messages import Error
from django.db.models.deletion import CASCADE
from .utils.model_mapper import ModelMapper
from django.db import models
import json, sys, uuid

sys.path.append("..")
from errors.client_error import AuthorizationError, ClientError, NotFoundError
from users.models import User

class Workspace(models.Model):
    class Meta:
        db_table = '"workspaces"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=32)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "owner": self.owner,
        }

class WorkspaceMember(models.Model):
    class Meta:
        db_table = '"workspace_members"'

    class MemberStatus(models.IntegerChoices):
        INVITED = 1
        PENDING = 2
        JOINED = 3

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    email = models.EmailField(unique=True, max_length=254, null=True)
    status = models.IntegerField(choices=MemberStatus.choices, default=1, null=False)

    def __str__(self):
        return json.dumps({
            "uuid": self.uuid,
            "workspace_id": self.workspace_id,
            "member_id": self.member_id,
        })

class Folder(models.Model):
    class Meta:
        db_table = '"folders"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=32)
    workspace_uuid = models.ForeignKey(Workspace, on_delete=models.CASCADE)

class List(models.Model):
    class Meta:
        db_table = '"lists"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=32)
    folder_uuid = models.ForeignKey(Folder, on_delete=models.CASCADE)

class Story(models.Model):
    class Meta:
        db_table = '"stories"'

    class PriorityChoices(models.IntegerChoices):
        LOW = 1
        MEDIUM = 2
        HIGH = 3
    
    class StatusChoices(models.IntegerChoices):
        TODO = 1
        IN_PROGRESS = 2
        IN_REVIEW = 3
        IN_EVALUATION = 4
        DONE = 5

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, blank=False, null=True)
    desc = models.CharField(max_length=500, blank=True, null=True)
    priority = models.IntegerField(choices=PriorityChoices.choices, default=1, null=False)
    status = models.IntegerField(choices=StatusChoices.choices, default=1, null=False)
    list_uuid = models.ForeignKey(List, on_delete=models.CASCADE)

class Task(models.Model):
    class Meta:
        db_table = '"tasks"'

    class PriorityChoices(models.IntegerChoices):
        LOW = 1
        MEDIUM = 2
        HIGH = 3
    
    class StatusChoices(models.IntegerChoices):
        TODO = 1
        IN_PROGRESS = 2
        IN_REVIEW = 3
        IN_EVALUATION = 4
        DONE = 5

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, blank=False, null=True)
    desc = models.CharField(max_length=500, blank=True, null=True)
    priority = models.IntegerField(choices=PriorityChoices.choices, default=1, null=False)
    status = models.IntegerField(choices=StatusChoices.choices, default=1, null=False)
    story_uuid = models.ForeignKey(Story, on_delete=models.CASCADE)

class TaskAssignee(models.Model):
    class Meta:
        db_table = '"task_assignees"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_uuid = models.ForeignKey(Task, on_delete=models.CASCADE)
    workspace_member_uuid = models.ForeignKey(WorkspaceMember, on_delete=models.CASCADE)

class SubTask(models.Model):
    class Meta:
        db_table = '"subtasks"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, blank=False, null=True)
    is_done = models.BooleanField(default=False, editable=False)
    task_uuid = models.ForeignKey(Task, on_delete=models.CASCADE)
    assignee_uuid = models.ForeignKey(TaskAssignee, null=True, on_delete=models.CASCADE)
