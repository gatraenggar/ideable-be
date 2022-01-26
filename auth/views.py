from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import json, jwt, sys, uuid

from .models import Authentication
from .utils.password_manager import PasswordManager
from .utils.token_manager import TokenManager
from .validators import OAuthSignForm, RegistrationForm, LoginForm, ResendEmailForm
from .services.rabbitmq.email_confirmation import send_confirmation_email
from .services.oauth.oauth import OAuth

from .use_cases.post_register_user import post_register_user
from .use_cases.post_verify_user_email import post_verify_user_email
from .use_cases.post_login_oauth import post_login_oauth
from .use_cases.post_login_email import post_login_email
from .use_cases.post_logout import post_logout
from .use_cases.get_login_oauth import get_login_oauth
from .use_cases.get_oauth_user_consent import get_oauth_user_consent
from .use_cases.get_verification_email import get_verification_email


sys.path.append("..")
from users.models import User
from errors.client_error import AuthenticationError, ClientError, ConflictError, NotFoundError
from errors.handler import errorResponse

class AuthView(generic.ListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

class RegisterView(AuthView):
    def post(self, request):
        try:
            payload = json.loads(request.body)
            payload["email"] = payload["email"].strip()

            isPayloadValid = RegistrationForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            registerUserResp = post_register_user(payload)

            response = JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "User has successfully registered",
                    "data": {
                        "first_name": registerUserResp["first_name"],
                        "last_name": registerUserResp["last_name"],
                        "is_confirmed": registerUserResp["is_confirmed"],
                    }
                }
            )

            response.set_cookie(
                key="access_token",
                value=registerUserResp["access_token"],
                max_age=None,
                expires=None,
                httponly=True
            )
            response.set_cookie(
                key="refresh_token",
                value=registerUserResp["refresh_token"],
                max_age=None,
                expires=None,
                httponly=True
            )

            return response
        except Exception as e:
            return errorResponse(e)

class EmailVerificationView(AuthView):
    def get(self, request):
        try:
            payload = json.loads(request.body)
            payload["email"] = payload["email"].strip()

            isPayloadValid = ResendEmailForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")
            payload["token"] = token

            get_verification_email(payload)

            return JsonResponse(
                status = 202,
                data = {
                    "status": "success",
                    "message": "An email verification has successfully re-sent",
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, _, auth_token):
        try:
            post_verify_user_email(auth_token)

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Email has successfully verified",
                }
            )
        except Exception as e:
            return errorResponse(e)

class OAuthView(AuthView):
    def get(self, _):
        try:
            authURI = get_oauth_user_consent()

            return redirect(authURI)

        except Exception as e:
            return errorResponse(e)

class OAuthCallbackView(AuthView):
    def get(self, request):
        try:
            authCode = request.GET.get("code")
            
            loginOauthResp = get_login_oauth({"auth_code": authCode})

            return JsonResponse(
                status = loginOauthResp["status_code"],
                data = {
                    "status": "success",
                    "message": "OAuth success",
                    "data": {
                        "access_token": loginOauthResp["accessToken"],
                        "refresh_token": loginOauthResp["refreshToken"],
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

    def post(self, request):
        try:
            payload = json.loads(request.body)

            payload["email"] = payload["email"].strip()
            payload["first_name"]= payload["first_name"] if "first_name" in payload else ""
            payload["last_name"]= payload["last_name"] if "last_name" in payload else ""
            payload["is_oauth"]= True

            isPayloadValid = OAuthSignForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            loginOauthResp = post_login_oauth(payload)

            response = JsonResponse(
                status = loginOauthResp["status_code"],
                data = {
                    "status": "success",
                    "message": "OAuth success",
                    "data": {
                        "first_name": loginOauthResp["first_name"],
                        "last_name": loginOauthResp["last_name"],
                        "is_confirmed": loginOauthResp["is_confirmed"],
                    }
                }
            )

            response.set_cookie(
                key="access_token",
                value=loginOauthResp["accessToken"],
                max_age=None,
                expires=None,
                httponly=True
            )
            response.set_cookie(
                key="refresh_token",
                value=loginOauthResp["refreshToken"],
                max_age=None,
                expires=None,
                httponly=True
            )

            return response
        except Exception as e:
            return errorResponse(e)

class LoginView(AuthView):
    def post(self, request):
        try:
            payload = json.loads(request.body)
            payload["email"] = payload["email"].strip()

            isPayloadValid = LoginForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            loginEmailResp = post_login_email(payload)

            response = JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Login success",
                    "data": {
                        "first_name": loginEmailResp["first_name"],
                        "last_name": loginEmailResp["last_name"],
                        "is_confirmed": loginEmailResp["is_confirmed"],
                    }
                }
            )

            response.set_cookie(
                key="access_token",
                value=loginEmailResp["accessToken"],
                max_age=None,
                expires=None,
                httponly=True
            )
            response.set_cookie(
                key="refresh_token",
                value=loginEmailResp["refreshToken"],
                max_age=None,
                expires=None,
                httponly=True
            )

            return response
        except Exception as e:
            return errorResponse(e)

class LogoutView(AuthView):
    def post(self, request):
        try:
            refreshToken = request.COOKIES.get('refresh_token')
            
            post_logout({"refresh_token": refreshToken})

            response = JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Logout success",
                }
            )

            if request.COOKIES.get('access_token') != "":
                response.delete_cookie(key='access_token')

            if request.COOKIES.get('refresh_token') != "":
                response.delete_cookie(key='refresh_token')

            return response
        except Exception as e:
            return errorResponse(e)

class AuthTokenView(AuthView):
    def get(self, request):
        try:
            refreshToken = request.COOKIES.get('refresh_token')

            logoutResp = post_logout({"refresh_token": refreshToken})

            response = JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Access token has successfully generated",
                }
            )

            response.set_cookie(
                key="access_token",
                value=logoutResp["access_token"],
                max_age=None,
                expires=None,
                httponly=True
            )

            return response
        except Exception as e:
            return errorResponse(e)

class AuthUserStatus(AuthView):
    def get(self, request):
        try:
            token = request.COOKIES.get('access_token')
            
            TokenManager.verify_access_token(token)

            response = JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Access token is valid",
                }
            )

            return response
        except Exception as e:
            return errorResponse(e)
