from auth.models import Authentication
from auth.utils.token_manager import TokenManager
from errors.client_error import AuthenticationError, NotFoundError
import jwt, uuid

def post_renew_access_token(payload: dict):
    userData = None
    try: 
        userData = TokenManager.verify_refresh_token(payload["refresh_token"])
    except Exception as e:
        if isinstance(e, (jwt.ExpiredSignatureError)): raise AuthenticationError('Re-login required')
        raise e

    refreshToken = Authentication.objects.filter(refresh_token=payload["refresh_token"]).values()
    if refreshToken == None: raise NotFoundError("Refresh token not found")            

    userUUID = uuid.UUID(userData["user_uuid"])
    accessToken = TokenManager.generate_access_token(userUUID.hex)

    return {
        "access_token": accessToken,
    }
