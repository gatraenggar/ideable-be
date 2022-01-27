from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, NotFoundError
from users.models import User
from workspaces.models import Workspace, Folder, WorkspaceMember
import uuid

def get_folders(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    folderList = []

    if len(payload["workspace_ids"]) > 0:
        workspacesIDs = payload["workspace_ids"].split(",")
        user = User.objects.filter(uuid=userUUID).values("uuid", "email")
        if not len(user): raise AuthenticationError("User is not authenticated")

        workspaces = Workspace.objects.filter(uuid__in=workspacesIDs).values("owner_id")
        if not len(workspaces): raise NotFoundError("Workspace not found")
        
        if workspaces[0]["owner_id"] != user[0]["uuid"]: 
            workspaceMembers = WorkspaceMember.objects.filter(
                workspace__in=workspacesIDs,
                email=user[0]["email"],
            ).values("status")

            if not len(workspaceMembers) or workspaceMembers[0]["status"] == 1:
                raise AuthorizationError("Action is forbidden")

        folders = Folder.objects.filter(workspace_uuid__in=workspacesIDs).values("uuid", "name", "workspace_uuid")

        for folder in folders:
            folderList.append({
                "uuid": folder["uuid"],
                "name": folder["name"],
                "workspace_uuid": folder["workspace_uuid"],
            })

    return {
        "folders": folderList,
    }
