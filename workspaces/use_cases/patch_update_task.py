from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, ClientError, NotFoundError
from workspaces.models import Workspace, Task
from workspaces.validators import TaskForm
import uuid

def patch_update_task(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    patchPayload = payload["patch"]
    isPayloadvalid = TaskForm(patchPayload).is_patch_valid()
    if isPayloadvalid == False: raise ClientError("Invalid input")

    updated = Task.objects.filter(uuid=payload["task_uuid"]).update(**patchPayload)
    if updated == 0: raise ClientError("Story not found")

    tasks = Task.objects.filter(uuid=payload["task_uuid"]).values("uuid", "name", "desc", "priority", "status")

    return {
        "task": tasks[0]
    }
