from auth.utils.token_manager import TokenManager
from errors.client_error import AuthorizationError, ClientError, NotFoundError
from workspaces.models import Workspace, List, Story
from workspaces.validators import StoryForm
import uuid

def post_create_story(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"]).values("owner_id")
    if not len(workspace): raise NotFoundError("Workspace not found")
    if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

    storyPayload = {
        "name": payload["name"],
        "desc": payload["desc"],
        "priority": payload["priority"],
        "status": payload["status"],
        "list_uuid": List(uuid=payload["list_uuid"]),
    }

    isPayloadValid = StoryForm(storyPayload).is_patch_valid()
    if not isPayloadValid: raise ClientError("Invalid input")

    newStory = Story(**storyPayload)
    newStory.save()

    stories = Story.objects.filter(uuid=newStory.uuid).values("uuid", "name", "desc", "priority", "status")

    return {
        "story": stories[0]
    }
