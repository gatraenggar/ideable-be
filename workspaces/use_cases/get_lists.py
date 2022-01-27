from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, Folder, List
import uuid

def get_lists(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    listList = []

    if len(payload["workspace_ids"]) > 0 or len(payload["folder_ids"]) > 0:
        workspaceIDs = payload["workspace_ids"].split(",")
        folderIDs = payload["folder_ids"].split(",")

        user = User.objects.filter(uuid=userUUID).values("uuid", "email")
        if not len(user): raise AuthenticationError("User is not authenticated")

        workspaces = Workspace.objects.filter(uuid__in=workspaceIDs).values("uuid", "owner_id")
        if not len(workspaces): raise NotFoundError("Workspace not found")

        verifiedWorkspaceIDs = []
        memberWorkspaceIDs = []
        for workspace in workspaces:
            if workspace["owner_id"] != user[0]["uuid"]:
                memberWorkspaceIDs.append(workspace["uuid"])
            else:
                verifiedWorkspaceIDs.append(workspace["uuid"])

        if len(memberWorkspaceIDs):
            workspaceMember = WorkspaceMember.objects.filter(
                workspace__in=memberWorkspaceIDs,
                email=user[0]["email"],
            ).values("workspace", "status")

            for member in workspaceMember:
                if member["status"] != 1:
                    verifiedWorkspaceIDs.append(member["workspace"])

        folders = Folder.objects.filter(uuid__in=folderIDs).values("uuid", "workspace_uuid")
        verifiedFolderIDs = []
        for folder in folders:
            if folder["workspace_uuid"] in verifiedWorkspaceIDs:
                verifiedFolderIDs.append(folder["uuid"])

        lists = List.objects.filter(folder_uuid__in=verifiedFolderIDs).values("uuid", "name", "folder_uuid")

        for listObj in lists:
            listList.append({
                "uuid": listObj["uuid"],
                "name": listObj["name"],
                "folder_uuid": listObj["folder_uuid"],
            })

    return {
        "lists": listList,
    }
