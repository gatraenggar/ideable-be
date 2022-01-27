from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, NotFoundError, ClientError
from workspaces.models import Workspace, TaskAssignee
import uuid

def delete_task_assignee(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])
    
    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    isUnassignedTask = TaskAssignee.objects.filter(uuid=payload["assignee_uuid"]).delete()[0]
    if isUnassignedTask == 0: raise ClientError("Assignee not found")
