from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, Task
import uuid

def get_tasks(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    user = User.objects.filter(uuid=userUUID).values("uuid", "email")
    if not len(user): raise AuthenticationError("User is not authenticated")

    workspace = Workspace.objects.filter(uuid__in=payload["workspace_ids"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    
    if workspace[0]["owner_id"] != user[0]["uuid"]: 
        workspaceMember = WorkspaceMember.objects.filter(
            workspace__in=payload["workspace_ids"],
            email=user[0]["email"],
        ).values("status")

        if not len(workspaceMember) or workspaceMember[0]["status"] == 1:
            raise AuthorizationError("Action is forbidden")

    tasks = Task.objects.filter(
        story_uuid__in=payload["story_ids"]
    ).values("uuid", "name", "desc", "priority", "status")

    taskArr = []
    for task in tasks:
        taskArr.append({
            "uuid": task["uuid"],
            "name": task["name"],
            "desc": task["desc"],
            "priority": task["priority"],
            "status": task["status"],
        })

    return {
        "tasks": taskArr,
    }
