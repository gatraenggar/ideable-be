from .utils.model_mapper import ModelMapper
from django.db import models
import json, sys, uuid

sys.path.append("..")
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

    def get_workspaces(user_uuid):
        workspaceModel = Workspace.objects.filter(owner=user_uuid).values()
        if len(workspaceModel) < 1: return []

        workspaces = ModelMapper.to_workspace_list(workspaceModel)

        return workspaces

    def get_workspace_by_uuid(workspace_uuid):
        workspaceModel = Workspace.objects.filter(uuid=workspace_uuid).values()
        if len(workspaceModel) < 1: return {}

        workspace = ModelMapper.to_single_workspace(workspaceModel)

        return workspace
