from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, ClientError, NotFoundError
from workspaces.models import Workspace, Story, Task
from workspaces.validators import TaskForm
import uuid

def post_create_task(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    taskPayload = {
        "name": payload["name"],
        "desc": payload["desc"],
        "priority": payload["priority"],
        "status": payload["status"],
        "story_uuid": Story(uuid=payload["story_uuid"]),
    }

    isPayloadValid = TaskForm(taskPayload).is_patch_valid()
    if isPayloadValid == False: raise ClientError("Invalid input")

    newTask = Task(**taskPayload)
    newTask.save()

    tasks = Task.objects.filter(uuid=newTask.uuid).values("uuid", "name", "desc", "priority", "status")

    return {
        "task": tasks[0]
    }
