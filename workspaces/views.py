from .models import Folder, List, Story, SubTask, Task, TaskAssignee, Workspace, WorkspaceMember
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
            token = request.COOKIES.get('access_token')
            
            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspaces = Workspace.objects.filter(owner=userUUID).values("uuid", "name")

            workspaceList = []
            for workspace in workspaces:
                workspaceList.append({
                    "uuid": workspace["uuid"],
                    "name": workspace["name"],
                })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Get user's workspaces",
                    "data": workspaceList,
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid")
            if not len(user): raise AuthenticationError("User is not authenticated")

            payload = json.loads(request.body)
            payload["owner"] = User(uuid=userUUID)

            isPayloadValid = WorkspaceForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input. Characters length is 2-32.")

            newWorkspace = Workspace(**payload)
            newWorkspace.save()
            newWorkspace.refresh_from_db

            workspace = Workspace.objects.filter(uuid=newWorkspace.uuid).values("uuid", "name")

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully created",
                    "data": workspace[0]
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceDetailView(WorkspaceView):
    def get(self, request, workspace_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            ownerUUID = uuid.UUID(userData["user_uuid"])
            
            workspace = Workspace.objects.filter(uuid=workspace_uuid, owner=ownerUUID).values("uuid", "name")
            if not len(workspace): raise NotFoundError("Workspace not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Get user's workspace by ID",
                    "data": workspace[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def put(self, request, workspace_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])
            
            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["owner"] = userUUID

            isPayloadValid = WorkspaceForm(payload).is_valid()
            if not isPayloadValid: return ClientError("Invalid input")

            updated = Workspace.objects.filter(uuid=workspace_uuid).update(name=payload["name"])
            if updated == 0: raise ClientError("Workspace not found")

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("uuid", "name")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully updated",
                    "data": workspace[0]
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            isWorkspaceDeleted = Workspace.objects.filter(uuid=workspace_uuid).delete()[0]
            if isWorkspaceDeleted == 0: raise NotFoundError("Workspace not found")

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

            user = User.objects.filter(email=authPayload["email"]).values("uuid", "is_confirmed")
            if not len(user):
                try:
                    workspaceMember = WorkspaceMember.objects.get(
                        workspace=authPayload["workspace_uuid"],
                        email=authPayload["email"],
                    )
                    if workspaceMember.status == WorkspaceMember.MemberStatus.JOINED: raise ClientError("Request invalid")

                    workspaceMember.status = WorkspaceMember.MemberStatus.PENDING
                    workspaceMember.save(update_fields=["status"])
                    
                    return redirect("http://localhost:3000/register")
                except Exception as e:
                    if isinstance(e, WorkspaceMember.DoesNotExist): raise ClientError("Invitation expired")

            WorkspaceMember.update_member_status(
                workspace=authPayload["workspace_uuid"],
                email=authPayload["email"],
                status=WorkspaceMember.MemberStatus.JOINED,
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
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid", "is_confirmed")
            if not len(user): raise ClientError("User not found")
            if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            workspace = Workspace.objects.filter(uuid=workspace_uuid, owner=user[0]["uuid"]).values("uuid")
            if not len(workspace): raise NotFoundError("Workspace not found")

            payload = json.loads(request.body)
            isPayloadValid = WorkspaceMemberForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            user = User.objects.filter(email=payload["email"]).values("uuid")
            if len(user):
                workspaceMember = WorkspaceMember.objects.filter(
                    workspace=workspace_uuid,
                    email=payload["email"],
                    status=3,
                ).values("uuid")
                if len(workspaceMember): raise ClientError("User is already the member")

            tokenPayload = {
                "workspace_uuid": workspace_uuid.hex,
                "email": payload["email"],
            }
            emailAuthToken = TokenManager.generate_random_token(tokenPayload)

            workspaceMember = WorkspaceMember(
                workspace=Workspace(uuid=workspace_uuid),
                email=payload["email"],
                status=1,
            )
            workspaceMember.save()

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
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            payload = json.loads(request.body)
            isPayloadValid = WorkspaceMemberForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            user = User.objects.filter(uuid=userUUID).values("uuid", "is_confirmed")
            if not len(user): raise ClientError("User not found")
            if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            workspace = Workspace.objects.filter(uuid=workspace_uuid, owner=userUUID).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")

            isMemberDeleted = WorkspaceMember.objects.filter(workspace=workspace_uuid, email=payload["email"]).delete()[0]
            if isMemberDeleted == 0: raise NotFoundError("Member not found")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Member has succesfully removed",
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceFolderCreatorView(WorkspaceView):
    def post(self, request, workspace_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["workspace_uuid"] = Workspace(uuid=workspace_uuid)

            isPayloadValid = WorkspaceFolderForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            newFolder = Folder(**payload)
            newFolder.save()

            folder = Folder.objects.filter(uuid=newFolder.uuid).values("uuid", "name")

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Folder has successfully created",
                    "data": folder[0]
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceFolderView(WorkspaceView):
    def get(self, request):
        try:
            token = request.COOKIES.get('access_token')
            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            folderList = []

            workspacesIDsParam = request.GET.get('workspace_ids')
            if len(workspacesIDsParam) > 0:
                workspacesIDs = workspacesIDsParam.split(",")
                user = User.objects.filter(uuid=userUUID).values("uuid", "email")
                if not len(user): raise AuthenticationError("User is not authenticated")

                workspaces = Workspace.objects.filter(uuid__in=workspacesIDs).values("owner_id")
                if not len(workspaces): raise NotFoundError("Workspace not found")
                
                if workspaces[0]["owner_id"] != user[0]["uuid"]: 
                    workspaceMembers = WorkspaceMember.objects.filter(
                        workspace__in=workspacesIDs,
                        email=user[0]["email"],
                    ).values("status")

                    if not len(workspaceMembers) or workspaceMembers[0]["status"] == 1:
                        raise AuthorizationError("Action is forbidden")

                folders = Folder.objects.filter(workspace_uuid__in=workspacesIDs).values("uuid", "name", "workspace_uuid")

                for folder in folders:
                    folderList.append({
                        "uuid": folder["uuid"],
                        "name": folder["name"],
                        "workspace_uuid": folder["workspace_uuid"],
                    })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving workspace's folder",
                    "data": folderList,
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceFolderDetailView(WorkspaceView):
    def put(self, request, workspace_uuid, folder_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["workspace_uuid"] = Workspace(uuid=workspace_uuid)

            isPayloadValid = WorkspaceFolderForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")
 
            updated = Folder.objects.filter(uuid=folder_uuid).update(name=payload["name"])
            if updated == 0: raise ClientError("Folder not found")

            folder = Folder.objects.filter(uuid=folder_uuid).values("uuid", "name")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Folder has successfully updated",
                    "data": folder[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, folder_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            isFolderDeleted = Folder.objects.filter(uuid=folder_uuid).delete()[0]
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

class WorkspaceListCreatorView(WorkspaceView):
    def post(self, request, workspace_uuid, folder_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["folder_uuid"] = Folder(uuid=folder_uuid)

            isPayloadValid = WorkspaceListForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            newList = List(**payload)
            newList.save()

            theList = List.objects.filter(uuid=newList.uuid).values("uuid", "name")

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "List has successfully created",
                    "data": theList[0]
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceListView(WorkspaceView):
    def get(self, request):
        try:
            token = request.COOKIES.get('access_token')
            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            listList = []

            workspacesIDsParam = request.GET.get('workspace_ids')
            folderIDsParam = request.GET.get('folder_ids')
            if len(workspacesIDsParam) > 0 or len(folderIDsParam) > 0:
                workspaceIDs = workspacesIDsParam.split(",")
                folderIDs = folderIDsParam.split(",")

                user = User.objects.filter(uuid=userUUID).values("uuid", "email")
                if not len(user): raise AuthenticationError("User is not authenticated")

                workspaces = Workspace.objects.filter(uuid__in=workspaceIDs).values("uuid", "owner_id")
                if not len(workspaces): raise NotFoundError("Workspace not found")

                verifiedWorkspaceIDs = []
                memberWorkspaceIDs = []
                for workspace in workspaces:
                    if workspace["owner_id"] != user[0]["uuid"]:
                        memberWorkspaceIDs.append(workspace["uuid"])
                    else:
                        verifiedWorkspaceIDs.append(workspace["uuid"])

                if len(memberWorkspaceIDs):
                    workspaceMember = WorkspaceMember.objects.filter(
                        workspace__in=memberWorkspaceIDs,
                        email=user[0]["email"],
                    ).values("workspace", "status")

                    for member in workspaceMember:
                        if member["status"] != 1:
                            verifiedWorkspaceIDs.append(member["workspace"])

                folders = Folder.objects.filter(uuid__in=folderIDs).values("uuid", "workspace_uuid")
                verifiedFolderIDs = []
                for folder in folders:
                    if folder["workspace_uuid"] in verifiedWorkspaceIDs:
                        verifiedFolderIDs.append(folder["uuid"])

                lists = List.objects.filter(folder_uuid__in=verifiedFolderIDs).values("uuid", "name", "folder_uuid")

                for listObj in lists:
                    listList.append({
                        "uuid": listObj["uuid"],
                        "name": listObj["name"],
                        "folder_uuid": listObj["folder_uuid"],
                    })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving folder's lists",
                    "data": listList,
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceListDetailView(WorkspaceView):
    def put(self, request, workspace_uuid, list_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid")
            if not len(user): raise AuthenticationError("User is not authenticated")

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != user[0]["uuid"]: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)

            isPayloadValid = WorkspaceListForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            updated = List.objects.filter(uuid=list_uuid).update(name=payload["name"])
            if updated == 0: raise ClientError("Folder not found")

            theList = List.objects.filter(uuid=list_uuid.uuid).values("uuid", "name")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "List has successfully updated",
                    "data": theList[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, list_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid")
            if not len(user): raise AuthenticationError("User is not authenticated")

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != user[0]["uuid"]: raise AuthorizationError("Action is forbidden")

            isListDeleted = List.objects.filter(uuid=list_uuid).delete()[0]
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

class StoryCreatorView(WorkspaceView):
    def post(self, request, workspace_uuid, list_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["list_uuid"] = List(uuid=list_uuid)

            isPayloadValid = StoryForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            newStory = Story(**payload)
            newStory.save()

            story = Story.objects.filter(uuid=newStory.uuid).values("uuid", "name", "desc", "priority", "status")

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Story has successfully created",
                    "data": story[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

class StoryView(WorkspaceView):
    def get(self, request):
        try:
            token = request.COOKIES.get('access_token')
            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            storyList = []

            workspacesIDsParam = request.GET.get('workspace_ids')
            listIDsParam = request.GET.get('list_ids')
            if len(workspacesIDsParam) > 0 or len(listIDsParam) > 0:
                workspaceIDs = workspacesIDsParam.split(",")
                listIDs = listIDsParam.split(",")

                user = User.objects.filter(uuid=userUUID).values("uuid", "email")
                if not len(user): raise AuthenticationError("User is not authenticated")

                workspaces = Workspace.objects.filter(uuid__in=workspaceIDs).values("owner_id")
                if not len(workspaces): raise NotFoundError("Workspace not found")
                
                if workspaces[0]["owner_id"] != user[0]["uuid"]: 
                    workspaceMembers = WorkspaceMember.objects.filter(
                        workspace=workspaceIDs,
                        email=user[0]["email"],
                    ).values("status")

                    if not len(workspaceMembers) or workspaceMembers[0]["status"] == 1:
                        raise AuthorizationError("Action is forbidden")

                stories = Story.objects.filter(
                    list_uuid__in=listIDs
                ).values("uuid", "name", "desc", "priority", "status")

                for story in stories:
                    storyList.append({
                        "uuid": story["uuid"],
                        "name": story["name"],
                        "desc": story["desc"],
                        "priority": story["priority"],
                        "status": story["status"],
                    })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving list's stories",
                    "data": storyList,
                }
            )
        except Exception as e:
            return errorResponse(e)

class StoryDetailView(WorkspaceView):
    def patch(self, request, workspace_uuid, story_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            isPayloadvalid = StoryForm(payload).is_patch_valid()
            if isPayloadvalid == False: raise ClientError("Invalid input")

            updated = Story.objects.filter(uuid=story_uuid).update(**payload)
            if updated == 0: raise ClientError("Story not found")
            
            story = Story.objects.filter(uuid=story_uuid).values("uuid", "name", "desc", "priority", "status")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Story has successfully updated",
                    "data": story[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, story_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            isStoryDeleted = Story.objects.filter(uuid=story_uuid).delete()[0]
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

class TaskCreatorView(WorkspaceView):
    def post(self, request, workspace_uuid, story_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["story_uuid"] = Story(uuid=story_uuid)

            isPayloadValid = TaskForm(payload).is_valid()
            if isPayloadValid == False: raise ClientError("Invalid input")

            newTask = Task(**payload)
            newTask.save()

            task = Task.objects.filter(uuid=newTask.uuid).values("uuid", "name", "desc", "priority", "status")

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Task has successfully created",
                    "data": task[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

class TaskView(WorkspaceView):
    def get(self, request):
        try:
            token = request.COOKIES.get('access_token')
            workspaceIDs = (request.GET.get('workspace_ids').split(","))
            storyIDs = (request.GET.get('story_ids').split(","))

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid", "email")
            if not len(user): raise AuthenticationError("User is not authenticated")

            workspace = Workspace.objects.filter(uuid__in=workspaceIDs).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            
            if workspace[0]["owner_id"] != user[0]["uuid"]: 
                workspaceMember = WorkspaceMember.objects.filter(
                    workspace__in=workspaceIDs,
                    email=user[0]["email"],
                ).values("status")

                if not len(workspaceMember) or workspaceMember[0]["status"] == 1:
                    raise AuthorizationError("Action is forbidden")

            tasks = Task.objects.filter(
                story_uuid__in=storyIDs
            ).values("uuid", "name", "desc", "priority", "status")

            taskList = []
            for task in tasks:
                taskList.append({
                    "uuid": task["uuid"],
                    "name": task["name"],
                    "desc": task["desc"],
                    "priority": task["priority"],
                    "status": task["status"],
                })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving story's tasks",
                    "data": taskList,
                }
            )
        except Exception as e:
            return errorResponse(e)

class TaskDetailView(WorkspaceView):
    def patch(self, request, workspace_uuid, task_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            isPayloadvalid = TaskForm(payload).is_patch_valid()
            if isPayloadvalid == False: raise ClientError("Invalid input")

            updated = Task.objects.filter(uuid=task_uuid).update(**payload)
            if updated == 0: raise ClientError("Story not found")

            task = Task.objects.filter(uuid=task_uuid).values("uuid", "name", "desc", "priority", "status")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Task has successfully updated",
                    "data": task[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, task_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid, owner=userUUID).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            isTaskDeleted = Task.objects.filter(uuid=task_uuid).delete()[0]
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
    def post(self, request, workspace_uuid, task_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            workspace = Workspace.objects.filter(uuid=workspace_uuid, owner=userUUID).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["task_uuid"] = Task(uuid=task_uuid)

            isPayloadValid = TaskAssigneeForm(payload).is_valid()
            if isPayloadValid == False: raise ClientError("Invalid input")

            memberInfo = User.objects.filter(uuid=uuid.UUID(payload["workspace_member_uuid"])).values("email")
            if not len(memberInfo): raise ClientError("Member is not found")

            workspaceMember = WorkspaceMember.objects.filter(email=memberInfo["email"]).values("uuid")
            if not len(workspaceMember): raise ClientError("Member is not valid")

            newAssignee = TaskAssignee(
                task_uuid=payload["task_uuid"],
                workspace_member_uuid=WorkspaceMember(uuid=workspaceMember[0]["uuid"])
            )
            newAssignee.save()

            assignee = TaskAssignee.objects.filter(uuid=newAssignee.uuid).values("uuid", "workspace_member_uuid")

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Task has succesfully assigned to member",
                    "data": assignee[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def get(self, request, workspace_uuid, task_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid", "email", "is_confirmed")
            if not len(user): raise ClientError("User not found")
            if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            
            if workspace[0]["owner_id"] != user[0]["uuid"]: 
                workspaceMember = WorkspaceMember.objects.filter(
                    workspace=Workspace(uuid=workspace_uuid),
                    email=user[0]["email"],
                ).values("status")

                if not len(workspaceMember) or workspaceMember[0]["status"] == WorkspaceMember.MemberStatus.INVITED:
                    raise AuthorizationError("Action is forbidden")

            assignees = TaskAssignee.objects.filter(task_uuid=task_uuid).values("uuid", "workspace_member_uuid")

            assigneeList = []
            for assignee in assignees:
                assigneeList.append({
                    "uuid": assignee["uuid"],
                    "workspace_member_uuid": assignee["workspace_member_uuid_id"],
                })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Task has succesfully assigned to member",
                    "data": {
                        "assignees": assigneeList,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, assignee_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])
            
            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            if workspace[0]["owner_id"] != userUUID: raise AuthorizationError("Action is forbidden")

            isUnassignedTask = TaskAssignee.objects.filter(uuid=assignee_uuid).delete()[0]
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
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid", "email", "is_confirmed")
            if not len(user): raise ClientError("User not found")
            if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            
            if workspace[0]["owner_id"] != user[0]["uuid"]: 
                workspaceMember = WorkspaceMember.objects.filter(
                    workspace=Workspace(uuid=workspace_uuid),
                    email=user[0]["email"],
                ).values("status")

                if not len(workspaceMember) or workspaceMember[0]["status"] == 1:
                    raise AuthorizationError("Action is forbidden")

            subtasks = SubTask.objects.filter(task_uuid=task_uuid).values("uuid", "name", "is_done", "assignee_uuid")

            subtaskList = []
            for subtask in subtasks:
                subtaskList.append({
                    "uuid": subtask["uuid"],
                    "name": subtask["name"],
                    "is_done": subtask["is_done"],
                    "assignee_uuid": subtask["assignee_uuid"],
                })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Sub-tasks has succesfully retrieved",
                    "data": {
                        "subtasks": subtaskList,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request, workspace_uuid, task_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid", "email", "is_confirmed")
            if not len(user): raise ClientError("User not found")
            if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            
            if workspace[0]["owner_id"] != user[0]["uuid"]: 
                workspaceMember = WorkspaceMember.objects.filter(
                    workspace=Workspace(uuid=workspace_uuid),
                    email=user[0]["email"],
                ).values("status")

                if not len(workspaceMember) or workspaceMember[0]["status"] == WorkspaceMember.MemberStatus.INVITED:
                    raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            payload["task_uuid"] = Task(uuid=task_uuid)

            isPayloadValid = SubTaskForm(payload).is_valid()
            if isPayloadValid == False: raise ClientError("Invalid input")

            newSubtask = SubTask(**payload)
            newSubtask.save()

            subtask = SubTask.objects.filter(uuid=newSubtask.uuid).values("uuid", "name", "is_done", "assignee_uuid")

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Sub-task has successfully created",
                    "data": subtask[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

class SubTaskDetailView(WorkspaceView):
    def patch(self, request, workspace_uuid, subtask_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid", "email", "is_confirmed")
            if not len(user): raise ClientError("User not found")
            if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            
            if workspace[0]["owner_id"] != user[0]["uuid"]: 
                workspaceMember = WorkspaceMember.objects.filter(
                    workspace=Workspace(uuid=workspace_uuid),
                    email=user[0]["email"],
                ).values("status")

                if not len(workspaceMember) or workspaceMember[0]["status"] == WorkspaceMember.MemberStatus.INVITED:
                    raise AuthorizationError("Action is forbidden")

            payload = json.loads(request.body)
            if "assignee_uuid" in payload and payload["assignee_uuid"] != None:
                payload["assignee_uuid"] = TaskAssignee(uuid=payload["assignee_uuid"])

            isPayloadvalid = SubTaskForm(payload).is_patch_valid()
            if isPayloadvalid == False: raise ClientError("Invalid input")

            updated = SubTask.objects.filter(uuid=subtask_uuid).update(**payload)
            if updated == 0: raise ClientError("Subtask not found")

            subtask = SubTask.objects.filter(uuid=subtask_uuid).values("uuid", "name", "is_done", "assignee_uuid")

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Sub-task has successfully updated",
                    "data": subtask[0],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, subtask_uuid):
        try:
            token = request.COOKIES.get('access_token')

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            user = User.objects.filter(uuid=userUUID).values("uuid", "is_confirmed")
            if not len(user): raise ClientError("User not found")
            if not user[0]["is_confirmed"]: raise AuthenticationError("User is not authenticated")                

            workspace = Workspace.objects.filter(uuid=workspace_uuid).values("owner_id")
            if not len(workspace): raise NotFoundError("Workspace not found")
            
            if workspace[0]["owner_id"] != user[0]["uuid"]: 
                workspaceMember = WorkspaceMember.objects.filter(
                    workspace=Workspace(uuid=workspace_uuid),
                    email=user[0]["email"],
                ).values("status")

                if not len(workspaceMember) or workspaceMember[0]["status"] == WorkspaceMember.MemberStatus.INVITED:
                    raise AuthorizationError("Action is forbidden")

            deletedSubtask = SubTask.objects.filter(uuid=subtask_uuid).delete()[0]
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
