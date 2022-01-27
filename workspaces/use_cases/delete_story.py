from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, NotFoundError, ClientError
from workspaces.models import Workspace, Story
import uuid

def delete_story(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    isStoryDeleted = Story.objects.filter(uuid=payload["story_uuid"]).delete()[0]
    if isStoryDeleted == 0: raise ClientError("Story not found")
