from math import fabs
from auth.utils.token_manager import TokenManager
from errors.client_error import ClientError
from users.models import User
from workspaces.models import WorkspaceMember
from decouple import config

def put_update_member_status(payload: dict):
    authPayload = TokenManager.verify_random_token(payload["auth_token"])

    user = User.objects.filter(email=authPayload["email"]).values("uuid", "is_confirmed")
    if not len(user):
        try:
            workspaceMember = WorkspaceMember.objects.get(
                workspace=authPayload["workspace_uuid"],
                email=authPayload["email"],
            )
            if workspaceMember.status == WorkspaceMember.MemberStatus.JOINED: raise ClientError("Request invalid")

            workspaceMember.status = WorkspaceMember.MemberStatus.PENDING
            workspaceMember.save(update_fields=["status"])
            
            return {
                "is_redirected": True,
                "target": (config("CLIENT") + "/register"),
            }
        except Exception as e:
            if isinstance(e, WorkspaceMember.DoesNotExist): raise ClientError("Invitation expired")

    WorkspaceMember.update_member_status(
        workspace=authPayload["workspace_uuid"],
        email=authPayload["email"],
        status=WorkspaceMember.MemberStatus.JOINED,
    )

    if not user["is_confirmed"]:
        return {
            "is_redirected": True,
            "target": (config("CLIENT") + "/profile"),
        }

    return {
        "is_redirected": False,
    }
