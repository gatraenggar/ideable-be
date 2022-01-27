from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, NotFoundError, ClientError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, SubTask
import uuid

def delete_subtask(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    user = User.objects.filter(uuid=userUUID).values("uuid", "is_confirmed")
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

    deletedSubtask = SubTask.objects.filter(uuid=payload["subtask_uuid"]).delete()[0]
    if deletedSubtask == 0: raise ClientError("Sub-task not found")
