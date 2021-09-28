from .models import Folder, Workspace, WorkspaceMember
from .services.rabbitmq.workspace_invitation import send_invitation_email
from .validators import WorkspaceForm, WorkspaceFolderForm, WorkspaceMemberForm
from django.http.response import JsonResponse
from django.shortcuts import redirect
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

            isOwnerTrue = Workspace.verify_owner(workspace_uuid, userUUID)
            if not isOwnerTrue: raise AuthorizationError("Action is forbidden")

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
                WorkspaceMember.update_member_status(
                    workspace=authPayload["workspace_uuid"],
                    email=authPayload["email"],
                    status=2,
                )
                return redirect("http://localhost:3000/register")

            WorkspaceMember.update_member_status(
                workspace=authPayload["workspace_uuid"],
                email=authPayload["email"],
                status=3,
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

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            isPayloadValid = WorkspaceMemberForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            workspace = Workspace.get_workspace_by_fields(uuid=workspace_uuid)
            if workspace == None: raise ClientError("Workspace not found")

            user = User.get_user_by_fields(email=payload["email"])
            if user != None:
                workspaceMember = WorkspaceMember.get_member_by_fields(
                    workspace=workspace_uuid,
                    email=payload["email"],
                    status=3,
                )
                if workspaceMember != None: raise ClientError("User is already the member")

            tokenPayload = {
                "workspace_uuid": workspace_uuid.hex,
                "email": payload["email"],
                "uri": "workspaces/" + str(uuid.UUID(workspace_uuid.hex)) + "/members/invitation/",
            }
            emailAuthToken = TokenManager.generate_random_token(tokenPayload)

            WorkspaceMember.add_workspace_member(
                workspace=Workspace(uuid=workspace_uuid),
                email=payload["email"],
                status=1,
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

    def delete(self, request, workspace_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            payload = json.loads(request.body)
            isPayloadValid = WorkspaceMemberForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            isOwnerTrue = Workspace.verify_owner(workspace_uuid, userUUID)
            if not isOwnerTrue: raise AuthorizationError("Action is forbidden")

            WorkspaceMember.remove_member(workspace_uuid, payload["email"])

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Member has succesfully removed",
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceFolderView(WorkspaceView):
    def get(self, request, workspace_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            isWorkspaceOwner = Workspace.verify_owner(workspace_uuid, user["uuid"])
            if isWorkspaceOwner == False:
                isWorkspaceMember = WorkspaceMember.verify_member(
                    workspace=Workspace(uuid=workspace_uuid),
                    email=user["email"],
                )

                if isWorkspaceMember == False: raise AuthorizationError("Action is forbidden")

            folders = Folder.get_folders_by_workspace(Workspace(uuid=workspace_uuid))

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving workspace's folder",
                    "data": folders,
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request, workspace_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["workspace_uuid"] = Workspace(uuid=workspace_uuid)

            isPayloadValid = WorkspaceFolderForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            folder_uuid = Folder.create_folder(**payload)

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Folder has successfully created",
                    "data": {
                        "folder_uuid": folder_uuid,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceFolderDetailView(WorkspaceView):
    def put(self, request, workspace_uuid, folder_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["workspace_uuid"] = Workspace(uuid=workspace_uuid)

            isPayloadValid = WorkspaceFolderForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            Folder.update_name(folder_uuid, payload["name"])

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully updated",
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, folder_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]): raise AuthorizationError("Action is forbidden")
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            isFolderDeleted = Folder.delete_folder(folder_uuid)
            if isFolderDeleted == 0: raise ClientError("Folder not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully deleted",
                }
            )
        except Exception as e:
            return errorResponse(e)
