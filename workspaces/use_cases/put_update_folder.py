from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, ClientError, NotFoundError
from workspaces.models import Workspace, Folder
from workspaces.validators import WorkspaceFolderForm
import uuid

def put_update_folder(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    folderPayload = {
        "name": payload["name"],
        "workspace_uuid": Workspace(uuid=payload["workspace_uuid"])
    }
    isPayloadValid = WorkspaceFolderForm(folderPayload).is_valid()
    if not isPayloadValid: raise ClientError("Invalid input")

    updated = Folder.objects.filter(uuid=payload["folder_uuid"]).update(name=folderPayload["name"])
    if updated == 0: raise ClientError("Folder not found")

    folder = Folder.objects.filter(uuid=payload["folder_uuid"]).values("uuid", "name")

    return {
        "folder": folder[0]
    }
