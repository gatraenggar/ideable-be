from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, NotFoundError, ClientError
from users.models import User
from workspaces.models import Workspace, List
import uuid

def delete_list(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    user = User.objects.filter(uuid=userUUID).values("uuid")
    if not len(user): raise AuthenticationError("User is not authenticated")

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != user[0]["uuid"]: raise AuthorizationError("Action is forbidden")

    isListDeleted = List.objects.filter(uuid=payload["list_uuid"]).delete()[0]
    if isListDeleted == 0: raise ClientError("List not found")
