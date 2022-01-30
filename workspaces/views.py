from django.http.response import JsonResponse
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

import json, sys

from .use_cases.get_workspaces import get_workspaces
from .use_cases.get_folders import get_folders
from .use_cases.get_lists import get_lists
from .use_cases.get_stories import get_stories
from .use_cases.get_tasks import get_tasks
from .use_cases.get_subtasks import get_subtasks
from .use_cases.get_task_assignees import get_task_assignees
from .use_cases.get_workspace_by_id import get_workspace_by_id
from .use_cases.post_create_workspace import post_create_workspace
from .use_cases.post_create_folder import post_create_folder
from .use_cases.post_create_list import post_create_list
from .use_cases.post_create_story import post_create_story
from .use_cases.post_create_task import post_create_task
from .use_cases.post_create_subtask import post_create_subtask
from .use_cases.post_add_task_assignee import post_add_task_assignee
from .use_cases.post_invite_workspace_member import post_invite_workspace_member
from .use_cases.put_update_workspace import put_update_workspace
from .use_cases.put_update_folder import put_update_folder
from .use_cases.put_update_list import put_update_list
from .use_cases.put_update_member_status import put_update_member_status
from .use_cases.patch_update_story import patch_update_story
from .use_cases.patch_update_task import patch_update_task
from .use_cases.patch_update_subtask import patch_update_subtask
from .use_cases.delete_workspace import delete_workspace
from .use_cases.delete_workspace_member import delete_workspace_member
from .use_cases.delete_folder import delete_folder
from .use_cases.delete_list import delete_list
from .use_cases.delete_story import delete_story
from .use_cases.delete_task import delete_task
from .use_cases.delete_subtask import delete_subtask
from .use_cases.delete_task_assignee import delete_task_assignee

sys.path.append("..")
from errors.handler import errorResponse

class WorkspaceView(generic.ListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        try:
            workspacesResp = get_workspaces({
                "token": request.COOKIES.get('access_token')
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Get user's workspaces",
                    "data": workspacesResp["workspaces"],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request):
        try:
            payload = json.loads(request.body)

            workspaceResp = post_create_workspace({
                "token": request.COOKIES.get('access_token'),
                "name": payload["name"],
            })

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully created",
                    "data": workspaceResp["workspace"],
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceDetailView(WorkspaceView):
    def get(self, request, workspace_uuid):
        try:
            workspaceByIDResp = get_workspace_by_id({
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Get user's workspace by ID",
                    "data": workspaceByIDResp["workspace"],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def put(self, request, workspace_uuid):
        try:
            payload = json.loads(request.body)

            updateWorkspaceResp = put_update_workspace({
                "token": request.COOKIES.get('access_token'),
                "name": payload["name"],
                "workspace_uuid": workspace_uuid,
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Workspace has successfully updated",
                    "data": updateWorkspaceResp["workspace"],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid):
        try:
            token = request.COOKIES.get('access_token')

            delete_workspace({
                "token": token,
                "workspace_uuid": workspace_uuid,
            })

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
    def put(self, _, workspace_uuid, auth_token):
        try:
            updateStatusResp = put_update_member_status({"auth_token": auth_token})
            if updateStatusResp["is_redirected"] == True:
                redirect(updateStatusResp["target"])

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
            payload = json.loads(request.body)

            post_invite_workspace_member({
                "token": request.COOKIES.get('access_token'),
                "email": payload["email"],
                "workspace_uuid": workspace_uuid,
            })

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
            payload = json.loads(request.body)

            delete_workspace_member({
                "email": payload["email"],
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
            })

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
            payload = json.loads(request.body)

            createFolderResp = post_create_folder({
                "token": request.COOKIES.get('access_token'),
                "name": payload["name"],
                "workspace_uuid": workspace_uuid,
            })

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Folder has successfully created",
                    "data": createFolderResp["folder"],
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceFolderView(WorkspaceView):
    def get(self, request):
        try:
            foldersResp = get_folders({
                "token": request.COOKIES.get('access_token'),
                "workspace_ids": request.GET.get('workspace_ids'),
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving workspace's folder",
                    "data": foldersResp["folders"],
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceFolderDetailView(WorkspaceView):
    def put(self, request, workspace_uuid, folder_uuid):
        try:
            payload = json.loads(request.body)

            updateFolderResp = put_update_folder({
                "token": request.COOKIES.get('access_token'),
                "name": payload["name"],
                "workspace_uuid": workspace_uuid,
                "folder_uuid": folder_uuid,
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Folder has successfully updated",
                    "data": updateFolderResp["folder"],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, folder_uuid):
        try:
            delete_folder({
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
                "folder_uuid": folder_uuid,
            })

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
            payload = json.loads(request.body)

            createListResp = post_create_list({
                "token": request.COOKIES.get('access_token'),
                "name": payload["name"],
                "workspace_uuid": workspace_uuid,
                "folder_uuid": folder_uuid,
            })

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "List has successfully created",
                    "data": createListResp["list"]
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceListView(WorkspaceView):
    def get(self, request):
        try:            
            listsResp = get_lists({
                "token": request.COOKIES.get('access_token'),
                "workspace_ids": request.GET.get('workspace_ids'),
                "folder_ids": request.GET.get('folder_ids'),
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving folder's lists",
                    "data": listsResp["lists"],
                }
            )
        except Exception as e:
            return errorResponse(e)

class WorkspaceListDetailView(WorkspaceView):
    def put(self, request, workspace_uuid, list_uuid):
        try:
            payload = json.loads(request.body)

            updateListResp = put_update_list({
                "token": request.COOKIES.get('access_token'),
                "payload": payload["name"],
                "workspace_uuid": workspace_uuid,
                "list_uuid": list_uuid,
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "List has successfully updated",
                    "data": updateListResp["list"],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, list_uuid):
        try:
            delete_list({
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
                "list_uuid": list_uuid,
            })

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
            payload = json.loads(request.body)

            createStoryResp = post_create_story({
                "token": request.COOKIES.get('access_token'),
                "story_req": payload,
                "list_uuid": list_uuid,
                "workspace_uuid": workspace_uuid,
            })
            
            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Story has successfully created",
                    "data": createStoryResp["story"],
                }
            )
        except Exception as e:
            return errorResponse(e)

class StoryView(WorkspaceView):
    def get(self, request):
        try:
            storiesResp = get_stories({
                "token": request.COOKIES.get('access_token'),
                "workspace_ids": request.GET.get('workspace_ids'),
                "list_ids": request.GET.get('list_ids'),
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving list's stories",
                    "data": storiesResp["stories"],
                }
            )
        except Exception as e:
            return errorResponse(e)

class StoryDetailView(WorkspaceView):
    def patch(self, request, workspace_uuid, story_uuid):
        try:
            updateStoryResp = patch_update_story({
                "token": request.COOKIES.get('access_token'),
                "patch": json.loads(request.body),
                "workspace_uuid": workspace_uuid,
                "story_uuid": story_uuid,
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Story has successfully updated",
                    "data": updateStoryResp["story"],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, story_uuid):
        try:
            delete_story({
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
                "story_uuid": story_uuid,
            })

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
            payload = json.loads(request.body)

            createTaskResp = post_create_task({
                "token": request.COOKIES.get('access_token'),
                "name": payload["name"],
                "desc": payload["desc"],
                "priority": payload["priority"],
                "status": payload["status"],
                "workspace_uuid": workspace_uuid,
                "story_uuid": story_uuid,
            })

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Task has successfully created",
                    "data": createTaskResp["task"],
                }
            )
        except Exception as e:
            return errorResponse(e)

class TaskView(WorkspaceView):
    def get(self, request):
        try:
            tasksResp = get_tasks({
                "token": request.COOKIES.get('access_token'),
                "workspace_ids": (request.GET.get('workspace_ids').split(",")),
                "story_ids": (request.GET.get('story_ids').split(",")),
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Success retrieving story's tasks",
                    "data": tasksResp["tasks"],
                }
            )
        except Exception as e:
            return errorResponse(e)

class TaskDetailView(WorkspaceView):
    def patch(self, request, workspace_uuid, task_uuid):
        try:
            updateTaskResp = patch_update_task({
                "token": request.COOKIES.get('access_token'),
                "patch": json.loads(request.body),
                "workspace_uuid": workspace_uuid,
                "task_uuid": task_uuid,
            })
            
            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Task has successfully updated",
                    "data": updateTaskResp["task"],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, task_uuid):
        try:
            delete_task({
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
                "task_uuid": task_uuid,
            })

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
            payload = json.loads(request.body)

            addTaskAssigneeResp = post_add_task_assignee({
                "token": request.COOKIES.get('access_token'),
                "workspace_member_uuid": payload["workspace_member_uuid"],
                "workspace_uuid": workspace_uuid,
                "task_uuid": task_uuid,
            })
            
            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Task has succesfully assigned to member",
                    "data": addTaskAssigneeResp["assignee"],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def get(self, request, workspace_uuid, task_uuid):
        try:
            taskAssigneesResp = get_task_assignees({
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
                "task_uuid": task_uuid,
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Task has succesfully assigned to member",
                    "data": taskAssigneesResp,
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, assignee_uuid):
        try:
            delete_task_assignee({
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
                "assignee_uuid": assignee_uuid,
            })

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
            subtaskResp = get_subtasks({
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
                "task_uuid": task_uuid,
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Sub-tasks has succesfully retrieved",
                    "data": subtaskResp,
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request, workspace_uuid, task_uuid):
        try:
            payload = json.loads(request.body)

            subtaskResp = post_create_subtask({
                "token": request.COOKIES.get('access_token'),
                "name": payload["name"],
                "workspace_uuid": workspace_uuid,
                "task_uuid": task_uuid,
            })

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "Sub-task has successfully created",
                    "data": subtaskResp["subtask"],
                }
            )
        except Exception as e:
            return errorResponse(e)

class SubTaskDetailView(WorkspaceView):
    def patch(self, request, workspace_uuid, subtask_uuid):
        try:
            updateSubtaskResp = patch_update_subtask({
                "token": request.COOKIES.get('access_token'),
                "patch": json.loads(request.body),
                "workspace_uuid": workspace_uuid,
                "subtask_uuid": subtask_uuid,
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Sub-task has successfully updated",
                    "data": updateSubtaskResp["subtask"],
                }
            )
        except Exception as e:
            return errorResponse(e)

    def delete(self, request, workspace_uuid, subtask_uuid):
        try:
            delete_subtask({
                "token": request.COOKIES.get('access_token'),
                "workspace_uuid": workspace_uuid,
                "subtask_uuid": subtask_uuid,
            })

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Sub-task has successfully deleted",
                }
            )
        except Exception as e:
            return errorResponse(e)
