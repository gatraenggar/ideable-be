from auth.utils.token_manager import TokenManager
from auth.services.rabbitmq.email_confirmation import send_confirmation_email

def get_verification_email(payload: dict):
    userData = TokenManager.verify_access_token(payload["token"])
    emailAuthToken = TokenManager.generate_random_token({ "user_uuid": userData["user_uuid"] })

    send_confirmation_email(payload["email"], emailAuthToken)
