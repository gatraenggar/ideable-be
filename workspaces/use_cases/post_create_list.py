from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, ClientError, NotFoundError
from workspaces.models import Workspace, Folder, List
from workspaces.validators import WorkspaceListForm
import uuid

def post_create_list(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    listPayload = {
        "name": payload["name"],
        "folder_uuid": Folder(uuid=payload["folder_uuid"]),
    }

    isPayloadValid = WorkspaceListForm(listPayload).is_valid()
    if not isPayloadValid: raise ClientError("Invalid input")

    newList = List(**listPayload)
    newList.save()

    lists = List.objects.filter(uuid=newList.uuid).values("uuid", "name")

    return {
        "list": lists[0]
    }
