from django.urls import path
from . import views

urlpatterns = [
    path('users/', views.UserView.as_view()),
    path('users/<uuid:user_uuid>/', views.UserDetailView.as_view()),
]
