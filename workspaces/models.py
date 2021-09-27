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
        workspace = workspaceQuery.values()
        
        if not len(workspace): raise NotFoundError("Workspace not found")
        if workspace[0]["owner_id"] != owner_uuid: raise AuthorizationError("Action is forbidden")

        result = workspaceQuery.delete()

        return result[0]

class WorkspaceMember(models.Model):
    class Meta:
        db_table = '"workspace_members"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    member = models.ForeignKey(User, on_delete=models.DO_NOTHING)

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

class WorkspaceMemberQueue(models.Model):
    class Meta:
        db_table = '"workspace_member_queues"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE)
    email = models.EmailField(unique=False, max_length=254)
    token = models.CharField(max_length=1000)

    def __str__(self):
        return json.dumps({
            "uuid": self.uuid,
            "workspace": self.workspace,
            "email": self.email,
            "token": self.token,
        })

    def create_membership_queue(workspace_uuid, email, token):
        memberQueueQuery = WorkspaceMemberQueue.objects.filter(
            workspace=workspace_uuid,
            email=email,
        )
        if len(memberQueueQuery.values()) != 0: memberQueueQuery.delete()[0]

        membershipQueue = WorkspaceMemberQueue(
            workspace=Workspace(uuid=workspace_uuid),
            email=email,
            token=token
        )
        membershipQueue.save()
        
        return membershipQueue.uuid

    def delete_queue(**payload):
        queueDeleted = WorkspaceMemberQueue.objects.filter(**payload).delete()[0]

        return queueDeleted
