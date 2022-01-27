from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, ClientError, NotFoundError
from users.models import User
from workspaces.models import Workspace
from workspaces.validators import WorkspaceForm
import json, uuid

def put_update_workspace(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])
    
    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    workspacePayload = {
        "name": payload["name"],
        "owner": userUUID,
    }

    isPayloadValid = WorkspaceForm(workspacePayload).is_valid()
    if not isPayloadValid: return ClientError("Invalid input")

    updated = Workspace.objects.filter(uuid=payload["workspace_uuid"]).update(name=payload["name"])
    if updated == 0: raise ClientError("Workspace not found")

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("uuid", "name")

    return {
        "workspace": workspace[0]
    }
