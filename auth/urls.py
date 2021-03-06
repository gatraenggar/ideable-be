from django.urls import path
from . import views

urlpatterns = [
    path('auth', views.AuthTokenView.as_view()),
    path('auth/register', views.RegisterView.as_view()),
    path('auth/login', views.LoginView.as_view()),
    path('auth/logout', views.LogoutView.as_view()),
    path('auth/email-resending', views.EmailVerificationView.as_view()),
    path('auth/email-verification/<str:auth_token>', views.EmailVerificationView.as_view()),
    path('oauth/google/login', views.OAuthView.as_view()),
    path('oauth/google/login/callback', views.OAuthCallbackView.as_view()),
    path('auth/user-status', views.AuthUserStatus.as_view()),
]
