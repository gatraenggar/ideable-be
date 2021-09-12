from django.urls import include, path

urlpatterns = [
    path('v1/', include('auth.urls')),
    path('v1/', include('users.urls')),
    path('v1/', include('workspaces.urls')),
]