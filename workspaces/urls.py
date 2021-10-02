from django.urls import path
from . import views

urlpatterns = [
    path('workspaces/', views.WorkspaceView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/', views.WorkspaceDetailView.as_view()),
    
    path('workspaces/<uuid:workspace_uuid>/folders/', views.WorkspaceFolderView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/<uuid:folder_uuid>/', views.WorkspaceFolderDetailView.as_view()),
    
    path('workspaces/<uuid:workspace_uuid>/folders/<uuid:folder_uuid>/lists/', views.WorkspaceListView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/<uuid:folder_uuid>/lists/<uuid:list_uuid>/', views.WorkspaceListDetailView.as_view()),

    path('workspaces/<uuid:workspace_uuid>/folders/<uuid:folder_uuid>/lists/<uuid:list_uuid>/stories/', views.StoryView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/<uuid:folder_uuid>/lists/<uuid:list_uuid>/stories/<uuid:story_uuid>/', views.StoryDetailView.as_view()),
    
    path('workspaces/<uuid:workspace_uuid>/stories/<uuid:story_uuid>/', views.TaskView.as_view()),

    path('workspaces/<uuid:workspace_uuid>/members/', views.WorkspaceMemberView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/members/invitation/<str:auth_token>', views.WorkspaceMemberView.as_view()),
]
