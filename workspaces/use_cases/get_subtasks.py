from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, ClientError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, SubTask
import uuid

def get_subtasks(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    user = User.objects.filter(uuid=userUUID).values("uuid", "email", "is_confirmed")
    if not len(user): raise ClientError("User not found")
    if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    
    if workspace[0]["owner_id"] != user[0]["uuid"]: 
        workspaceMember = WorkspaceMember.objects.filter(
            workspace=Workspace(uuid=payload["workspace_uuid"]),
            email=user[0]["email"],
        ).values("status")

        if not len(workspaceMember) or workspaceMember[0]["status"] == 1:
            raise AuthorizationError("Action is forbidden")

    subtasks = SubTask.objects.filter(task_uuid=payload["task_uuid"]).values("uuid", "name", "is_done", "assignee_uuid")

    subtaskList = []
    for subtask in subtasks:
        subtaskList.append({
            "uuid": subtask["uuid"],
            "name": subtask["name"],
            "is_done": subtask["is_done"],
            "assignee_uuid": subtask["assignee_uuid"],
        })

    return {
        "subtasks": subtaskList,
    }
