from auth.models import Authentication
from auth.services.rabbitmq.email_confirmation import send_confirmation_email
from auth.utils.password_manager import PasswordManager
from auth.utils.token_manager import TokenManager
from errors.client_error import ConflictError
from users.models import User

def post_register_user(payload: dict):
    registeredUser = User.objects.filter(email=payload["email"]).values("email")
    if len(registeredUser): raise ConflictError("Email already registered")

    payload["password"] = PasswordManager.hash(payload["password"])
    user = User(**payload)
    user.save()

    userUUID = user.uuid
    emailAuthToken = TokenManager.generate_random_token({ "user_uuid": userUUID.hex })
    send_confirmation_email(payload["email"], emailAuthToken)

    accessToken = TokenManager.generate_access_token(userUUID.hex)
    refreshToken = TokenManager.generate_refresh_token(userUUID.hex)

    Authentication(refreshToken).save()

    return {
        "first_name": payload["first_name"],
        "last_name": payload["last_name"],
        "is_confirmed": False,
        "access_token": accessToken,
        "refresh_token": refreshToken,
    }
