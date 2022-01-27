from auth.utils.token_manager import TokenManager
from errors.client_error import NotFoundError
from workspaces.models import Workspace
import uuid

def get_workspace_by_id(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    ownerUUID = uuid.UUID(userData["user_uuid"])
    
    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"], owner=ownerUUID).values("uuid", "name")
    if not len(workspace): raise NotFoundError("Workspace not found")

    return {
        "workspace": workspace[0],
    }
