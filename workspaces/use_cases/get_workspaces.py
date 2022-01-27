from auth.utils.token_manager import TokenManager
from workspaces.models import Workspace
import uuid

def get_workspaces(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspaces = Workspace.objects.filter(owner=userUUID).values("uuid", "name")

    workspaceList = []
    for workspace in workspaces:
        workspaceList.append({
            "uuid": workspace["uuid"],
            "name": workspace["name"],
        })

    return {
        "workspaces": workspaceList,
    }
