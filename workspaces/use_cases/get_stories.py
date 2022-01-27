from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, AuthorizationError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember, Story
import uuid

def get_stories(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    storyList = []

    if len(payload["workspace_ids"]) > 0 or len(payload["list_ids"]) > 0:
        workspaceIDs = payload["workspace_ids"].split(",")
        listIDs = payload["list_ids"].split(",")

        user = User.objects.filter(uuid=userUUID).values("uuid", "email")
        if not len(user): raise AuthenticationError("User is not authenticated")

        workspaces = Workspace.objects.filter(uuid__in=workspaceIDs).values("owner_id")
        if not len(workspaces): raise NotFoundError("Workspace not found")
        
        if workspaces[0]["owner_id"] != user[0]["uuid"]: 
            workspaceMembers = WorkspaceMember.objects.filter(
                workspace=workspaceIDs,
                email=user[0]["email"],
            ).values("status")

            if not len(workspaceMembers) or workspaceMembers[0]["status"] == 1:
                raise AuthorizationError("Action is forbidden")

        stories = Story.objects.filter(
            list_uuid__in=listIDs
        ).values("uuid", "name", "desc", "priority", "status")

        for story in stories:
            storyList.append({
                "uuid": story["uuid"],
                "name": story["name"],
                "desc": story["desc"],
                "priority": story["priority"],
                "status": story["status"],
            })

    return {
        "stories": storyList,
    }
