from auth.models import Authentication
from auth.services.rabbitmq.email_confirmation import send_confirmation_email
from auth.utils.token_manager import TokenManager
from errors.client_error import ConflictError
from users.models import User

def post_login_oauth(payload: dict):
    userUUID = None
    statusCode = None

    registeredUsers = User.objects.filter(email=payload["email"]).values("uuid", "is_oauth", "is_confirmed")
    if not len(registeredUsers): 
        user = User(**payload)
        user.save()

        statusCode = 201
        userUUID = user.uuid

        emailAuthToken = TokenManager.generate_random_token({ "user_uuid": userUUID.hex })
        send_confirmation_email(payload["email"], emailAuthToken)
    else:
        if registeredUsers[0]["is_oauth"]:
            userUUID = registeredUsers[0]["uuid"]
            statusCode = 200
        else: raise ConflictError("Email already registered")

    accessToken = TokenManager.generate_access_token(userUUID.hex)
    refreshToken = TokenManager.generate_refresh_token(userUUID.hex)

    Authentication(refreshToken).save()

    return {
        "status_code": statusCode,
        "access_token": accessToken,
        "refresh_token": refreshToken,

        "first_name": payload["first_name"],
        "last_name": payload["last_name"],
        "is_confirmed": registeredUsers[0]["is_confirmed"] if len(registeredUsers) == 1 else False,
    }
