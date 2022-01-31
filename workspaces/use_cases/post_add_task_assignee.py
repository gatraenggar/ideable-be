from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, ClientError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, Task, TaskAssignee
from workspaces.validators import TaskAssigneeForm
import uuid

def post_add_task_assignee(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspaces = Workspace.objects.filter(uuid=payload["workspace_uuid"], owner=userUUID).values("owner_id")
    if not len(workspaces): raise NotFoundError("Workspace not found")
    if workspaces[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    assigneePayload = {
        "task_uuid": Task(uuid=payload["task_uuid"]),
        "workspace_member_uuid": payload["workspace_member_uuid"],
    }

    isPayloadValid = TaskAssigneeForm(assigneePayload).is_valid()
    if isPayloadValid == False: raise ClientError("Invalid input")

    memberInfos = User.objects.filter(uuid=uuid.UUID(assigneePayload["workspace_member_uuid"])).values("email")
    if not len(memberInfos): raise ClientError("Member is not found")

    workspaceMembers = WorkspaceMember.objects.filter(email=memberInfos[0]["email"]).values("uuid")
    if not len(workspaceMembers): raise ClientError("Member is not valid")

    newAssignee = TaskAssignee(
        task_uuid=assigneePayload["task_uuid"],
        workspace_member_uuid=WorkspaceMember(uuid=workspaceMembers[0]["uuid"])
    )
    newAssignee.save()

    assignees = TaskAssignee.objects.filter(uuid=newAssignee.uuid).values("uuid", "workspace_member_uuid")

    return {
        "assignee": assignees[0]
    }
