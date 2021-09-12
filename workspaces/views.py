from .models import Workspace
from .validators import WorkspaceForm
from django.http.response import JsonResponse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import json, sys, uuid

sys.path.append("..")
from errors.client_error import ClientError
from errors.handler import errorResponse
from auth.utils.token_manager import TokenManager
from users.models import User

class WorkspaceView(generic.ListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def post(self, request):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")
            userData = TokenManager.verify_access_token(token)

            user = User.get_user_by_fields(uuid=uuid.UUID(userData["user_uuid"]))
            if user == None or not user["is_confirmed"]: raise ClientError("User is not authorized")

            payload = json.loads(request.body)
            payload["owner"] = User(uuid=user["uuid"])

            isPayloadValid = WorkspaceForm(payload).is_valid()
            if not isPayloadValid: return ClientError("Invalid input")

            workspace = Workspace(**payload)
            workspace.save()

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully created",
                    "data": {
                        "workspace_uuid": workspace.uuid
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)
