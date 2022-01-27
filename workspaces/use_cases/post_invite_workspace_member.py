from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, ClientError, NotFoundError
from users.models import User
from workspaces.models import Workspace, WorkspaceMember
from workspaces.services.rabbitmq.workspace_invitation import send_invitation_email
from workspaces.validators import WorkspaceMemberForm
import uuid

def post_invite_workspace_member(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    userUUID = uuid.UUID(userData["user_uuid"])

    user = User.objects.filter(uuid=userUUID).values("uuid", "is_confirmed")
    if not len(user): raise ClientError("User not found")
    if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

    workspace = Workspace.objects.filter(uuid=payload["workspace_uuid"], owner=user[0]["uuid"]).values("uuid")
    if not len(workspace): raise NotFoundError("Workspace not found")

    workspaceMemberPayload = { "email": payload["email"] }
    isPayloadValid = WorkspaceMemberForm(workspaceMemberPayload).is_valid()
    if not isPayloadValid: raise ClientError("Invalid input")

    user = User.objects.filter(email=workspaceMemberPayload["email"]).values("uuid")
    if len(user):
        workspaceMember = WorkspaceMember.objects.filter(
            workspace=payload["workspace_uuid"],
            email=workspaceMemberPayload["email"],
            status=3,
        ).values("uuid")
        if len(workspaceMember): raise ClientError("User is already the member")

    tokenPayload = {
        "workspace_uuid": payload["workspace_uuid"].hex,
        "email": payload["email"],
    }
    emailAuthToken = TokenManager.generate_random_token(tokenPayload)

    workspaceMember = WorkspaceMember(
        workspace=Workspace(uuid=payload["workspace_uuid"]),
        email=workspaceMemberPayload["email"],
        status=1,
    )
    workspaceMember.save()

    send_invitation_email(payload["email"], emailAuthToken)
