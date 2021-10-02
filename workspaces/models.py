from django.core.checks.messages import Error
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
        return json.dumps({
            "uuid": self.uuid,
            "name": self.name,
            "owner": self.owner,
        })

    def create_workspace(**payload):
        workspace = Workspace(**payload)
        workspace.save()

        return workspace.uuid        

    def verify_owner(workspace_uuid, user_uuid):
        workspace = Workspace.objects.filter(uuid=workspace_uuid).values()
        if not len(workspace): raise NotFoundError("Workspace not found")
        
        return True if workspace[0]["owner_id"] == user_uuid else False

    def get_workspaces(user_uuid):
        workspaceModel = Workspace.objects.filter(owner=user_uuid).values()
        if len(workspaceModel) < 1: return []

        workspaces = ModelMapper.to_workspace_list(workspaceModel)

        return workspaces

    def get_workspace_by_fields(**payload):
        workspaceModel = Workspace.objects.filter(**payload).values()
        if len(workspaceModel) < 1: return None

        workspace = ModelMapper.to_single_workspace(workspaceModel)

        return workspace

    def update_name(workspace_uuid, new_name, owner_uuid):
        workspace = Workspace.objects.filter(uuid=workspace_uuid).values()
        if len(workspace) != 1: raise ClientError("Workspace not found")

        if workspace[0]["owner_id"] != owner_uuid: raise AuthorizationError("Action is forbidden")

        workspace.update(name=new_name)

    def delete_workspace(workspace_uuid, owner_uuid):
        workspaceQuery = Workspace.objects.filter(uuid=workspace_uuid)

        result = workspaceQuery.delete()

        return result[0]

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

    def add_workspace_member(**payload):
        workspaceMember = WorkspaceMember(**payload)
        workspaceMember.save()

        return workspaceMember.uuid

    def get_member_by_fields(**payload):
        workspaceMember = WorkspaceMember.objects.filter(**payload).values()
        if not len(workspaceMember): return None

        return workspaceMember

    def verify_member(workspace, email):
        workspaceMember = WorkspaceMember.objects.filter(workspace=workspace, email=email).values()
        return True if len(workspaceMember) and workspaceMember[0]["status"] != 1 else False

    def update_member_status(workspace, email, status):
        try:
            workspaceMember = WorkspaceMember.objects.get(workspace=workspace, email=email)
            if workspaceMember.status == 3: raise ClientError("Request invalid")

            workspaceMember.status = status
            workspaceMember.save(update_fields=["status"])

            return workspaceMember.uuid
        except Exception as e:
            if isinstance(e, WorkspaceMember.DoesNotExist): raise ClientError("Invitation expired")

    def remove_member(workspace, email):
        memberQuery = WorkspaceMember.objects.filter(workspace=workspace, email=email)        
        member = memberQuery.values()
        if not len(member): raise NotFoundError("Member not found")

        result = memberQuery.delete()

        return result[0]

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

class WorkspaceContent:
    def __init__(self, ContentModel) -> None:
        self.ContentModel = ContentModel

    def create_content(self, **payload):
        content = self.ContentModel(**payload)
        content.save()

        return content.uuid

    def get_contents_by_parent(self, **parent_uuid):
        contents = self.ContentModel.objects.filter(**parent_uuid).values()

        contentList = []
        for content in contents:
            contentList.append({
                "uuid": content["uuid"],
                "name": content["name"],
            })
        
        return contentList

    def update_name(self, content_uuid, new_name):
        updatedcontent = self.ContentModel.objects.filter(uuid=content_uuid).update(name=new_name)
        if updatedcontent == 0: raise ClientError("Folder not found")

    def delete_content(self, content_uuid):
        return self.ContentModel.objects.filter(uuid=content_uuid).delete()[0]

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
    name = models.CharField(max_length=50, blank=False, null=True)
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

class ListContent:
    def __init__(self, ContentModel) -> None:
        self.ContentModel = ContentModel

    def create_item(self, **payload):
        content = self.ContentModel(**payload)
        content.save()

        return content.uuid

    def get_items_by_parent(self, **parent_uuid):
        contents = self.ContentModel.objects.filter(**parent_uuid).values()

        contentList = []
        for content in contents:
            contentList.append({
                "uuid": content["uuid"],
                "name": content["name"],
                "desc": content["desc"],
                "priority": content["priority"],
                "status": content["status"],
            })
        
        return contentList

    def update_fields(self, content_uuid, **payload):
        updatedcontent = self.ContentModel.objects.filter(uuid=content_uuid).update(**payload)
        if updatedcontent == 0: raise ClientError("Story not found")

    def delete_item(self, content_uuid):
        return self.ContentModel.objects.filter(uuid=content_uuid).delete()[0]
