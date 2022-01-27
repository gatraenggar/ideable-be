from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, ClientError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, Task, TaskAssignee
from workspaces.validators import TaskAssigneeForm
import uuid

def post_add_task_assignee(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"], owner=userUUID).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    assigneePayload = {
        "task_uuid": Task(uuid=payload["task_uuid"]),
        "workspace_member_uuid": payload["workspace_member_uuid"],
    }

    isPayloadValid = TaskAssigneeForm(assigneePayload).is_valid()
    if isPayloadValid == False: raise ClientError("Invalid input")

    memberInfo = User.objects.filter(uuid=uuid.UUID(assigneePayload["workspace_member_uuid"])).values("email")
    if not len(memberInfo): raise ClientError("Member is not found")

    workspaceMember = WorkspaceMember.objects.filter(email=memberInfo["email"]).values("uuid")
    if not len(workspaceMember): raise ClientError("Member is not valid")

    newAssignee = TaskAssignee(
        task_uuid=assigneePayload["task_uuid"],
        workspace_member_uuid=WorkspaceMember(uuid=workspaceMember[0]["uuid"])
    )
    newAssignee.save()

    assignees = TaskAssignee.objects.filter(uuid=newAssignee.uuid).values("uuid", "workspace_member_uuid")

    return {
        "assignee": assignees[0]
    }
