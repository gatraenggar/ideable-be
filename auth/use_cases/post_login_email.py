from auth.models import Authentication
from auth.utils.password_manager import PasswordManager
from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError
from users.models import User

def post_login_email(payload: dict):
    users = User.objects.filter(email=payload["email"]).values(
        "uuid",
        "password",
        "first_name",
        "last_name",
        "is_oauth",
        "is_confirmed"
    )
    if len(users) != 1 or users[0]["is_oauth"]: raise AuthenticationError("Email or password doesn't match any account")

    user = users[0]
    isPasswordTrue = PasswordManager.verify(user["password"], payload["password"])
    if not isPasswordTrue: raise AuthenticationError("Email or password doesn't match any account")

    accessToken = TokenManager.generate_access_token(user["uuid"].hex)
    refreshToken = TokenManager.generate_refresh_token(user["uuid"].hex)

    Authentication(refreshToken).save()

    return {
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "is_confirmed": user["is_confirmed"],
        "access_token": accessToken,
        "refresh_token": refreshToken,
    }
