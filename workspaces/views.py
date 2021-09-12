from django.core.checks.messages import Error
from .models import Workspace
from .validators import WorkspaceForm
from django.http.response import JsonResponse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import json, sys, uuid

sys.path.append("..")
from errors.client_error import AuthenticationError, AuthorizationError, ClientError, NotFoundError
from errors.handler import errorResponse
from auth.utils.token_manager import TokenManager
from users.models import User

class WorkspaceView(generic.ListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")
            userData = TokenManager.verify_access_token(token)

            userUUID = uuid.UUID(userData["user_uuid"])
            workspaces = Workspace.get_workspaces(userUUID)

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Get user's workspaces",
                    "data": workspaces,
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")
            userData = TokenManager.verify_access_token(token)

            user = User.get_user_by_fields(uuid=uuid.UUID(userData["user_uuid"]))
            if user == None or not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

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

class WorkspaceDetailView(WorkspaceView):
    def get(self, request, workspace_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")
            userData = TokenManager.verify_access_token(token)

            ownerUUID = uuid.UUID(userData["user_uuid"])
            workspace = Workspace.get_workspace_by_uuid(workspace_uuid, ownerUUID)
            if workspace == None: raise NotFoundError("Workspace not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Get user's workspace by ID",
                    "data": workspace,
                }
            )
        except Exception as e:
            return errorResponse(e)

    def put(self, request, workspace_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            payload = json.loads(request.body)
            payload["owner"] = User(uuid=userUUID)

            isPayloadValid = WorkspaceForm(payload).is_valid()
            if not isPayloadValid: return ClientError("Invalid input")

            Workspace.update_name(workspace_uuid, payload["name"], payload["owner"])

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully updated",
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            Workspace.delete_workspace(workspace_uuid, userUUID)

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully deleted",
                }
            )
        except Exception as e:
            return errorResponse(e)
