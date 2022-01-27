from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, ClientError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember
from workspaces.validators import WorkspaceMemberForm
import uuid

def delete_workspace_member(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspaceMemberPayload = { "email": payload["email"] }
    isPayloadValid = WorkspaceMemberForm(workspaceMemberPayload).is_valid()
    if not isPayloadValid: raise ClientError("Invalid input")

    user = User.objects.filter(uuid=userUUID).values("uuid", "is_confirmed")
    if not len(user): raise ClientError("User not found")
    if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"], owner=userUUID).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")

    isMemberDeleted = WorkspaceMember.objects.filter(workspace=payload["workspace_uuid"], email=workspaceMemberPayload["email"]).delete()[0]
    if isMemberDeleted == 0: raise NotFoundError("Member not found")
