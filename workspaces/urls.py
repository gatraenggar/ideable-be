from django.urls import path
from . import views

urlpatterns = [
    path('workspaces/', views.WorkspaceView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/', views.WorkspaceDetailView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/', views.WorkspaceFolderView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/folders/<uuid:folder_uuid>/', views.WorkspaceFolderDetailView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/members/', views.WorkspaceMemberView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/members/invitation/<str:auth_token>', views.WorkspaceMemberView.as_view()),
]
