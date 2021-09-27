from .models import Workspace, WorkspaceMember, WorkspaceMemberQueue
from .services.rabbitmq.workspace_invitation import send_invitation_email
from .validators import WorkspaceForm, WorkspaceMemberForm
from django.http.response import JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import json, sys, uuid

sys.path.append("..")
from errors.client_error import AuthenticationError, ClientError, NotFoundError
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

            workspaceUUID = Workspace.create_workspace(**payload)

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully created",
                    "data": {
                        "workspace_uuid": workspaceUUID
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
            workspace = Workspace.get_workspace_by_fields(uuid=workspace_uuid, owner=ownerUUID)
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
            payload["owner"] = userUUID

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

class WorkspaceMemberView(WorkspaceView):
    def get(self, _, workspace_uuid, auth_token):
        try:
            authPayload = TokenManager.verify_random_token(auth_token)

            user = User.get_user_by_fields(email=authPayload["email"])
            if user == None:
                WorkspaceMemberQueue.set_pending_join(auth_token)
                return redirect("http://localhost:3000/register")

            isQueueDeleted = WorkspaceMemberQueue.delete_queue(token=auth_token)
            if not isQueueDeleted: raise ClientError("Request invalid")

            WorkspaceMember.add_workspace_member(
                workspace=Workspace(uuid=workspace_uuid),
                member=User(uuid=user["uuid"]),
            )

            if not user["is_confirmed"]:
                return redirect("http://localhost:3000/profile")

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Workspace membership has successfully verified",
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request, workspace_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            ownerData = TokenManager.verify_access_token(token)
            owner = User.get_user_by_fields(uuid=ownerData["user_uuid"])
            if not owner["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            payload = json.loads(request.body)
            isPayloadValid = WorkspaceMemberForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            workspace = Workspace.get_workspace_by_fields(uuid=workspace_uuid)
            if workspace == None: raise ClientError("Workspace not found")

            user = User.get_user_by_fields(email=payload["email"])
            if user != None:
                workspaceMember = WorkspaceMember.get_member_by_fields(
                    workspace=workspace_uuid,
                    member=User(uuid=user["uuid"])
                )
                if workspaceMember != None: raise ClientError("User is already the member")

            tokenPayload = {
                "workspace_uuid": workspace_uuid.hex,
                "email": payload["email"],
                "uri": "workspaces/" + str(uuid.UUID(workspace_uuid.hex)) + "/members/",
            }
            emailAuthToken = TokenManager.generate_random_token(tokenPayload)

            WorkspaceMemberQueue.create_membership_queue(
                workspace_uuid=workspace_uuid,
                email=payload["email"],
                token=emailAuthToken,
            )

            send_invitation_email(payload["email"], emailAuthToken)

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Invitation email has successfully sent to user",
                }
            )
        except Exception as e:
            return errorResponse(e)
