from .client_error import ClientError, ConflictError, NotFoundError
from django.http import JsonResponse
import jwt

def errorResponse(errorInstance):
    print(errorInstance)
    if isinstance(errorInstance, (
        ClientError,
        ConflictError,
        NotFoundError,
    )):
        return JsonResponse(
            status = errorInstance.statusCode,
            data = {
                "status": "failed",
                "message": str(errorInstance)
            }
        )
    elif isinstance(errorInstance, (jwt.ExpiredSignatureError)):
        return JsonResponse(
            status = 401,
            data = {
                "status": "failed",
                "message": "Request has expired"
            }
        )
    elif isinstance(errorInstance, (jwt.InvalidSignatureError)):
        return JsonResponse(
            status = 401,
            data = {
                "status": "failed",
                "message": "Token invalid"
            }
        ) 
    else:
        return JsonResponse(
            status = 500,
            data = {
                "status": "failed",
                "message": "Internal server error"
            }
        )
