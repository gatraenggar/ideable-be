from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, ClientError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, TaskAssignee
import uuid

def get_task_assignees(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    users = User.objects.filter(uuid=userUUID).values("uuid", "email", "is_confirmed")
    if not len(users): raise ClientError("User not found")
    if not users[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

    workspaces = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspaces): raise NotFoundError("Workspace not found")
    
    if workspaces[0]["owner_id"] != users[0]["uuid"]: 
        workspaceMembers = WorkspaceMember.objects.filter(
            workspace=Workspace(uuid=payload["workspace_uuid"]),
            email=users[0]["email"],
        ).values("status")

        if not len(workspaceMembers) or workspaceMembers[0]["status"] == WorkspaceMember.MemberStatus.INVITED:
            raise AuthorizationError("Action is forbidden")

    assignees = TaskAssignee.objects.filter(task_uuid=payload["task_uuid"]).values("uuid", "workspace_member_uuid")

    assigneeArr = []
    for assignee in assignees:
        assigneeArr.append({
            "uuid": assignee["uuid"],
            "workspace_member_uuid": assignee["workspace_member_uuid"],
        })

    return {
        "assignees": assigneeArr,
    }
