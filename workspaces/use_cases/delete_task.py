from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, NotFoundError, ClientError
from workspaces.models import Workspace, Task
import uuid

def delete_task(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"], owner=userUUID).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    isTaskDeleted = Task.objects.filter(uuid=payload["task_uuid"]).delete()[0]
    if isTaskDeleted == 0: raise ClientError("Task not found")
