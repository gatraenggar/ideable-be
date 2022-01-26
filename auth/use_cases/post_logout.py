from auth.models import Authentication
from errors.client_error import NotFoundError

def post_logout(payload: dict):
    isDeleted = Authentication.objects.filter(refresh_token=payload["refresh_token"]).delete()[0]
    if not isDeleted: raise NotFoundError("Token not found")
