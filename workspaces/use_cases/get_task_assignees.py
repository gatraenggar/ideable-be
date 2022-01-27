from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, ClientError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, TaskAssignee
import uuid

def get_task_assignees(payload: dict):
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

        if not len(workspaceMember) or workspaceMember[0]["status"] == WorkspaceMember.MemberStatus.INVITED:
            raise AuthorizationError("Action is forbidden")

    assignees = TaskAssignee.objects.filter(task_uuid=payload["task_uuid"]).values("uuid", "workspace_member_uuid")

    assigneeArr = []
    for assignee in assignees:
        assigneeArr.append({
            "uuid": assignee["uuid"],
            "workspace_member_uuid": assignee["workspace_member_uuid_id"],
        })

    return {
        "assignees": assigneeArr,
    }
