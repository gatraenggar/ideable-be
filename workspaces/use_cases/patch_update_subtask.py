from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, ClientError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, SubTask, TaskAssignee
from workspaces.validators import SubTaskForm
import uuid

def patch_update_subtask(payload: dict):
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

    patchPayload = payload["patch"]
    if "assignee_uuid" in patchPayload and patchPayload["assignee_uuid"] != None:
        patchPayload["assignee_uuid"] = TaskAssignee(uuid=patchPayload["assignee_uuid"])

    isPayloadvalid = SubTaskForm(patchPayload).is_patch_valid()
    if isPayloadvalid == False: raise ClientError("Invalid input")

    updated = SubTask.objects.filter(uuid=payload["subtask_uuid"]).update(**patchPayload)
    if updated == 0: raise ClientError("Subtask not found")

    subtask = SubTask.objects.filter(uuid=payload["subtask_uuid"]).values("uuid", "name", "is_done", "assignee_uuid")

    return {
        "subtask": subtask[0]
    }
