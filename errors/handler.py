from .client_error import ClientError, ConflictError, NotFoundError
from django.http import JsonResponse
import jwt

def errorResponse(errorInstance):
    statusCode = 500
    message = "Internal server error"

    print(errorInstance)
    if isinstance(errorInstance, (
        ClientError,
        ConflictError,
        NotFoundError,
    )):
        statusCode = errorInstance.statusCode
        message = str(errorInstance)

    elif isinstance(errorInstance, (jwt.ExpiredSignatureError)):
        statusCode = 401
        message = "Request has expired"

    elif isinstance(errorInstance, (jwt.InvalidSignatureError)):
        statusCode = 401
        message = "Token invalid"
        
    else:
        statusCode = 500
        message = "Internal server error"

    return JsonResponse(
        status = statusCode,
        data = {
            "status": "failed",
            "message": message
        }
    )
