from .models import Folder, List, ListContent, Story, SubTask, Task, TaskAssignee, Workspace, WorkspaceContent, WorkspaceMember
from .services.rabbitmq.workspace_invitation import send_invitation_email
from .validators import StoryForm, SubTaskForm, TaskAssigneeForm, TaskForm, WorkspaceForm, WorkspaceFolderForm, WorkspaceListForm, WorkspaceMemberForm
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

            folders = WorkspaceContent(Folder).get_contents_by_parent(workspace_uuid=Workspace(uuid=workspace_uuid))

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

            folderUUID = WorkspaceContent(Folder).create_content(**payload)

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Folder has successfully created",
                    "data": {
                        "folder_uuid": folderUUID,
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

            WorkspaceContent(Folder).update_name(folder_uuid, payload["name"])

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Folder has successfully updated",
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

            isFolderDeleted = WorkspaceContent(Folder).delete_content(folder_uuid)
            if isFolderDeleted == 0: raise ClientError("Folder not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Folder has successfully deleted",
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceListView(WorkspaceView):
    def get(self, request, workspace_uuid, folder_uuid):
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

            lists = WorkspaceContent(List).get_contents_by_parent(folder_uuid=Folder(uuid=folder_uuid))

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving folder's lists",
                    "data": lists,
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request, workspace_uuid, folder_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["folder_uuid"] = Folder(uuid=folder_uuid)

            isPayloadValid = WorkspaceListForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            listUUID = WorkspaceContent(List).create_content(**payload)

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "List has successfully created",
                    "data": {
                        "list_uuid": listUUID,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceListDetailView(WorkspaceView):
    def put(self, request, workspace_uuid, folder_uuid, list_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["folder_uuid"] = Folder(uuid=folder_uuid)

            isPayloadValid = WorkspaceListForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            WorkspaceContent(List).update_name(list_uuid, payload["name"])

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "List has successfully updated",
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, folder_uuid, list_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]): raise AuthorizationError("Action is forbidden")
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            isListDeleted = WorkspaceContent(List).delete_content(list_uuid)
            if isListDeleted == 0: raise ClientError("List not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "List has successfully deleted",
                }
            )
        except Exception as e:
            return errorResponse(e)

class StoryView(WorkspaceView):
    def get(self, request, workspace_uuid, folder_uuid, list_uuid):
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

            stories = ListContent(Story).get_items_by_parent(list_uuid=List(uuid=list_uuid))

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving list's stories",
                    "data": stories,
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request, workspace_uuid, folder_uuid, list_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["list_uuid"] = List(uuid=list_uuid)

            isPayloadValid = StoryForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            storyUUID = ListContent(Story).create_item(**payload)

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Story has successfully created",
                    "data": {
                        "story_uuid": storyUUID,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

class StoryDetailView(WorkspaceView):
    def patch(self, request, workspace_uuid, folder_uuid, list_uuid, story_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            isPayloadvalid = StoryForm(payload).is_patch_valid()
            if isPayloadvalid == False: raise ClientError("Invalid input")

            ListContent(Story).update_fields(story_uuid, **payload)

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Story has successfully updated",
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, folder_uuid, list_uuid, story_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]): raise AuthorizationError("Action is forbidden")
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            isStoryDeleted = ListContent(Story).delete_item(story_uuid)
            if isStoryDeleted == 0: raise ClientError("Story not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Story has successfully deleted",
                }
            )
        except Exception as e:
            return errorResponse(e)

class TaskView(WorkspaceView):
    def get(self, request, workspace_uuid, story_uuid):
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

            tasks = ListContent(Task).get_items_by_parent(story_uuid=Story(uuid=story_uuid))

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving story's tasks",
                    "data": tasks,
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request, workspace_uuid, story_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["story_uuid"] = Story(uuid=story_uuid)

            isPayloadValid = TaskForm(payload).is_valid()
            if isPayloadValid == False: raise ClientError("Invalid input")

            taskUUID = ListContent(Task).create_item(**payload)

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Task has successfully created",
                    "data": {
                        "task_uuid": taskUUID,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

class TaskDetailView(WorkspaceView):
    def patch(self, request, workspace_uuid, story_uuid, task_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            isPayloadvalid = TaskForm(payload).is_patch_valid()
            if isPayloadvalid == False: raise ClientError("Invalid input")

            ListContent(Task).update_fields(task_uuid, **payload)

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Task has successfully updated",
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, story_uuid, task_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]): raise AuthorizationError("Action is forbidden")
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            isTaskDeleted = ListContent(Task).delete_item(task_uuid)
            if isTaskDeleted == 0: raise ClientError("Task not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Task has successfully deleted",
                }
            )
        except Exception as e:
            return errorResponse(e)

class TaskAssigneeView(WorkspaceView):
    def post(self, request, workspace_uuid, story_uuid, task_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["task_uuid"] = Task(uuid=task_uuid)

            isPayloadValid = TaskAssigneeForm(payload).is_valid()
            if isPayloadValid == False: raise ClientError("Invalid input")

            memberInfo = User.get_user_by_fields(uuid=uuid.UUID(payload["workspace_member_uuid"]))
            if memberInfo == None: raise ClientError("Member is not found")

            workspace_member = WorkspaceMember.get_member_by_fields(email=memberInfo["email"])
            if workspace_member == None: raise ClientError("Member is not valid")

            assigneeUUID = TaskAssignee.assign_member(
                task_uuid=payload["task_uuid"],
                workspace_member_uuid=WorkspaceMember(uuid=workspace_member[0]["uuid"]),
            )

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Task has succesfully assigned to member",
                    "data": {
                        "assignee_uuid": assigneeUUID,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

    def get(self, request, workspace_uuid, story_uuid, task_uuid):
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

            assignees = TaskAssignee.get_assignees_by_task(task_uuid)

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Task has succesfully assigned to member",
                    "data": {
                        "assignees": assignees,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, assignee_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            isUnassignedTask = TaskAssignee.unassign_member(assignee_uuid)
            if isUnassignedTask == 0: raise ClientError("Assignee not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Member has successfully unassigned from task",
                }
            )
        except Exception as e:
            return errorResponse(e)

class SubTaskView(WorkspaceView):
    def get(self, request, workspace_uuid, task_uuid):
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

            subtasks = SubTask.get_subtasks_by_task(task_uuid)

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Sub-tasks has succesfully retrieved",
                    "data": {
                        "subtasks": subtasks,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request, workspace_uuid, task_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["task_uuid"] = Task(uuid=task_uuid)

            isPayloadValid = SubTaskForm(payload).is_valid()
            if isPayloadValid == False: raise ClientError("Invalid input")

            subtaskUUID = SubTask.create_task(**payload)

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Sub-task has successfully created",
                    "data": {
                        "subtask_uuid": subtaskUUID,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

class SubTaskDetailView(WorkspaceView):
    def patch(self, request, workspace_uuid, subtask_uuid):
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

            payload = json.loads(request.body)
            if "assignee_uuid" in payload and payload["assignee_uuid"] != None:
                payload["assignee_uuid"] = TaskAssignee(uuid=payload["assignee_uuid"])

            isPayloadvalid = SubTaskForm(payload).is_patch_valid()
            if isPayloadvalid == False: raise ClientError("Invalid input")

            SubTask.update_fields(subtask_uuid, **payload)

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Sub-task has successfully updated",
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, subtask_uuid):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            user = User.get_user_by_fields(uuid=userData["user_uuid"])
            if not user["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            if not Workspace.verify_owner(workspace_uuid, user["uuid"]):
                raise AuthorizationError("Action is forbidden")

            deletedSubtask = SubTask.delete_subtask(subtask_uuid)
            if deletedSubtask == 0: raise ClientError("Sub-task not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Sub-task has successfully deleted",
                }
            )
        except Exception as e:
            return errorResponse(e)
