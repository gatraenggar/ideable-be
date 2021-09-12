from django.urls import path
from . import views

urlpatterns = [
    path('workspaces/', views.WorkspaceView.as_view()),
    path('workspaces/<uuid:workspace_uuid>/', views.WorkspaceDetailView.as_view()),
]
