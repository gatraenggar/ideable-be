from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, ClientError
from users.models import User
from workspaces.models import Workspace
from workspaces.validators import WorkspaceForm
import uuid

def post_create_workspace(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    user = User.objects.filter(uuid=userUUID).values("uuid")
    if not len(user): raise AuthenticationError("User is not authenticated")

    workspacePayload = {
        "name": payload["name"],
        "owner": User(uuid=userUUID),
    }

    isPayloadValid = WorkspaceForm(workspacePayload).is_valid()
    if not isPayloadValid: raise ClientError("Invalid input. Characters length is 2-32.")

    newWorkspace = Workspace(**workspacePayload)
    newWorkspace.save()
    newWorkspace.refresh_from_db

    workspace = Workspace.objects.filter(uuid=newWorkspace.uuid).values("uuid", "name")

    return {
        "workspace": workspace[0]
    }
