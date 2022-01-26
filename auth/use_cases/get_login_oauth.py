from auth.models import Authentication
from auth.services.oauth.oauth import OAuth
from auth.services.rabbitmq.email_confirmation import send_confirmation_email
from auth.utils.token_manager import TokenManager
from errors.client_error import ConflictError
from users.models import User

def get_login_oauth(payload: dict):
    userInfo = OAuth.request_user_info(payload["auth_code"])

    payload = {
        "email": userInfo["email"],
        "first_name": userInfo["given_name"] if "given_name" in userInfo else "",
        "last_name": userInfo["family_name"] if "family_name" in userInfo else "",
        "is_oauth": True,
    }

    userUUID = None
    statusCode = None

    registeredUser = User.objects.filter(email=payload["email"]).values("uuid", "is_oauth")
    if not len(registeredUser): 
        user = User(**payload)
        user.save()

        statusCode = 201
        userUUID = user.uuid

        emailAuthToken = TokenManager.generate_random_token({ "user_uuid": userUUID.hex })
        send_confirmation_email(payload["email"], emailAuthToken)
    else:
        if registeredUser[0]["is_oauth"]:
            userUUID = registeredUser[0]["uuid"]
            statusCode = 200
        else: raise ConflictError("Email already registered")

    accessToken = TokenManager.generate_access_token(userUUID.hex)
    refreshToken = TokenManager.generate_refresh_token(userUUID.hex)

    Authentication(refreshToken).save()

    return {
        "status_code": statusCode,
        "access_token": accessToken,
        "refresh_token": refreshToken,
    }
