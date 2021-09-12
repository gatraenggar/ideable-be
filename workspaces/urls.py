from django.urls import path
from . import views

urlpatterns = [
    path('workspaces/', views.WorkspaceView.as_view())
]
