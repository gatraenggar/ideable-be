from .client_error import ClientError, ConflictError, NotFoundError
from django.http import JsonResponse

def errorResponse(errorInstance):
    print(errorInstance)
    if isinstance(errorInstance, (ClientError, ConflictError, NotFoundError)):
        return JsonResponse(
            status = errorInstance.statusCode,
            data = {
                "status": "failed",
                "message": str(errorInstance)
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
