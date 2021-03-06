from django.urls import path
from . import views

urlpatterns = [
    path('workspaces', views.WorkspaceView.as_view()),
    path('workspaces/<uuid:workspace_uuid>', views.WorkspaceDetailView.as_view()),

    path('workspaces/<uuid:workspace_uuid>/members', views.WorkspaceMemberView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/members/invitation/<str:auth_token>', views.WorkspaceMemberView.as_view()),
    
    path('workspaces/folders', views.WorkspaceFolderView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders', views.WorkspaceFolderCreatorView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/<uuid:folder_uuid>', views.WorkspaceFolderDetailView.as_view()),

    path('workspaces/folders/lists', views.WorkspaceListView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/<uuid:folder_uuid>/lists', views.WorkspaceListCreatorView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/lists/<uuid:list_uuid>', views.WorkspaceListDetailView.as_view()),

    path('workspaces/folders/lists/stories', views.StoryView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/lists/<uuid:list_uuid>/stories', views.StoryCreatorView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/lists/stories/<uuid:story_uuid>', views.StoryDetailView.as_view()),

    path('workspaces/folders/lists/stories/tasks', views.TaskView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/lists/stories/<uuid:story_uuid>/tasks', views.TaskCreatorView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/lists/stories/tasks/<uuid:task_uuid>', views.TaskDetailView.as_view()),

    path('workspaces/<uuid:workspace_uuid>/folders/lists/stories/tasks/<uuid:task_uuid>/assignees', views.TaskAssigneeView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/lists/stories/tasks/assignees/<uuid:assignee_uuid>', views.TaskAssigneeView.as_view()),

    path('workspaces/<uuid:workspace_uuid>/folders/lists/stories/tasks/<uuid:task_uuid>/subtasks', views.SubTaskView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/lists/stories/tasks/subtasks/<uuid:subtask_uuid>', views.SubTaskDetailView.as_view()),
]
