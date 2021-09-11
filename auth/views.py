from .models import Authentications
from .utils.password_manager import PasswordManager
from .utils.token_manager import TokenManager
from .validators import RegistrationForm
from .services.rabbitmq.email_confirmation import send_confirmation_email
from .services.oauth.oauth import OAuth
from django.http import JsonResponse
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import json, sys

sys.path.append("..")
from users.models import User
from errors.client_error import ClientError, ConflictError
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

            registeredUser = User.get_user_by_field(email=payload["email"])
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

class OAuthView(AuthView):
    def get(self, _):
        authURI = OAuth.request_user_consent()

        return redirect(authURI)

class OAuthCallbackView(generic.ListView):
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

            registeredUser = User.get_user_by_field(email=payload["email"])
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
