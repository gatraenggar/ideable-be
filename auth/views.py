from .models import Authentications
from .utils.password_manager import PasswordManager
from .utils.token_manager import TokenManager
from .validators import RegistrationForm, LoginForm, ResendEmailForm
from .services.rabbitmq.email_confirmation import send_confirmation_email
from .services.oauth.oauth import OAuth
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import json, sys, uuid

sys.path.append("..")
from users.models import User
from errors.client_error import ClientError, ConflictError, NotFoundError
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

            registeredUser = User.get_user_by_fields(email=payload["email"])
            if registeredUser != None: raise ConflictError("Email already registered")

            payload["password"] = PasswordManager.hash(payload["password"])

            userUUID = User.register_user(payload)

            emailAuthToken = TokenManager.generate_random_token(userUUID)
            send_confirmation_email(payload["email"], emailAuthToken)

            accessToken = TokenManager.generate_access_token(userUUID)
            refreshToken = TokenManager.generate_refresh_token(userUUID)

            Authentications(refreshToken).save()

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "User has successfully registered",
                    "data": {
                        "access_token": accessToken,
                        "refresh_token": refreshToken,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

class EmailVerificationView(AuthView):
    def get(self, _, auth_token):
        try:
            verificationParam = TokenManager.verify_random_token(auth_token)

            User.confirm_user_email(verificationParam["user_uuid"])

            return JsonResponse({
                "status": "success",
                "message": "Email has successfully verified",
            })
        except Exception as e:
            return errorResponse(e)

    def post(self, request):
        try:
            payload = json.loads(request.body)
            payload["email"] = payload["email"].strip()

            isPayloadValid = ResendEmailForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_access_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            emailAuthToken = TokenManager.generate_random_token(userUUID)
            send_confirmation_email(payload["email"], emailAuthToken)

            return JsonResponse({
                "status": "success",
                "message": "An email verification has successfully re-sent",
            })
        except Exception as e:
            return errorResponse(e)

class OAuthView(AuthView):
    def get(self, _):
        authURI = OAuth.request_user_consent()

        return redirect(authURI)

class OAuthCallbackView(AuthView):
    def get(self, request):
        try:
            authCode = request.GET.get("code")
            userInfo = OAuth.request_user_info(authCode)

            payload = {
                "email": userInfo["email"],
                "first_name": userInfo["given_name"],
                "last_name": userInfo["family_name"],
                "is_oauth": True,
            }

            registeredUser = User.get_user_by_fields(email=payload["email"])
            if registeredUser != None: raise ConflictError("Email already registered")

            userUUID = User.register_user(payload)

            emailAuthToken = TokenManager.generate_random_token(userUUID)
            send_confirmation_email(payload["email"], emailAuthToken)

            accessToken = TokenManager.generate_access_token(userUUID)
            refreshToken = TokenManager.generate_refresh_token(userUUID)

            Authentications(refreshToken).save()

            return JsonResponse({
                "status": "success",
                "message": "OAuth success",
                "data": {
                    "access_token": accessToken,
                    "refresh_token": refreshToken,
                },
            })
        except Exception as e:
            return errorResponse(e)

class LoginView(AuthView):
    def post(self, request):
        try:
            payload = json.loads(request.body)
            payload["email"] = payload["email"].strip()

            isPayloadValid = LoginForm(payload).is_valid()
            if not isPayloadValid: raise ClientError("Invalid input")

            user = User.get_raw_user_by_email(payload["email"])
            if user is None: raise ClientError("Email is not registered")

            isPasswordTrue = PasswordManager.verify(user["password"], payload["password"])
            if not isPasswordTrue: raise ClientError("Wrong password")

            accessToken = TokenManager.generate_access_token(user["uuid"])
            refreshToken = TokenManager.generate_refresh_token(user["uuid"])

            Authentications(refreshToken).save()

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Login success",
                    "data": {
                        "access_token": accessToken,
                        "refresh_token": refreshToken,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

class LogoutView(AuthView):
    def post(self, request):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            isDeleted = Authentications.delete_refresh_token(token)
            if not isDeleted: raise NotFoundError("Token not found")

            return JsonResponse({
                "status": "success",
                "message": "Logout success",
            })
        except Exception as e:
            return errorResponse(e)

class AuthTokenView(AuthView):
    def get(self, request):
        try:
            bearerToken = request.headers["Authorization"]
            token = bearerToken.replace("Bearer ", "")

            userData = TokenManager.verify_refresh_token(token)
            userUUID = uuid.UUID(userData["user_uuid"])

            refreshToken = Authentications.get_refresh_token(token)
            if refreshToken == None: raise NotFoundError("Refresh token not found")            

            accessToken = TokenManager.generate_access_token(userUUID)

            return JsonResponse({
                "status": "success",
                "message": "Access token has successfully generated",
                "data": {
                    "access_token": accessToken,
                },
            })
        except Exception as e:
            return errorResponse(e)
