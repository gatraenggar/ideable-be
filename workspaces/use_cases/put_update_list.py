from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, ClientError, NotFoundError
from workspaces.models import Workspace, List
from users.models import User
from workspaces.validators import WorkspaceListForm
import uuid

def put_update_list(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    user = User.objects.filter(uuid=userUUID).values("uuid")
    if not len(user): raise AuthenticationError("User is not authenticated")

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != user[0]["uuid"]: raise AuthorizationError("Action is forbidden")

    isPayloadValid = WorkspaceListForm({"name": payload["name"]}).is_valid()
    if not isPayloadValid: raise ClientError("Invalid input")

    updated = List.objects.filter(uuid=payload["list_uuid"]).update(name=payload["name"])
    if updated == 0: raise ClientError("Folder not found")

    lists = List.objects.filter(uuid=payload["list_uuid"]).values("uuid", "name")

    return {
        "list": lists[0]
    }
