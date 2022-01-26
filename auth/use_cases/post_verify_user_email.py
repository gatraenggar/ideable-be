from auth.utils.token_manager import TokenManager

from users.models import User
from errors.client_error import ClientError


def post_verify_user_email(auth_token):
    tokenParam = TokenManager.verify_random_token(auth_token)

    user = User.objects.get(uuid=tokenParam["user_uuid"])
    if user.is_confirmed: raise ClientError("Request is no longer valid")

    user.is_confirmed = True
    user.save(update_fields=["is_confirmed"])
