from django import db
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

    def update_member_status(workspace, email, status):
        workspaceMember = WorkspaceMember.objects.get(workspace=workspace, email=email)
        if workspaceMember.status == 3: raise ClientError("Request invalid")

        workspaceMember.status = status
        workspaceMember.save(update_fields=["status"])

        return workspaceMember.uuid

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

    def create_folder(**payload):
        folder = Folder(**payload)
        folder.save()

        return folder.uuid

class List(models.Model):
    class Meta:
        db_table = '"lists"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=32)
    folder_uuid = models.ForeignKey(Folder, on_delete=models.CASCADE)

class FolderList(models.Model):
    class Meta:
        db_table = '"folder_lists"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder_uuid = models.ForeignKey(Folder, on_delete=models.CASCADE)
    list_uuid = models.ForeignKey(List, on_delete=models.CASCADE)
