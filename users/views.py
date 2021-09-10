from .models import User
from .utils.password_manager import PasswordManager
from .utils.model_mapper import ModelMapper
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
from errors.client_error import ClientError, ConflictError, NotFoundError
from errors.handler import errorResponse

class UserView(generic.ListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, _):
        users = User.get_users()

        return JsonResponse({
            "status": "success",
            "data": users
        })

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

            auth_token = TokenManager.encode({"user_uuid": userUUID.hex})
            send_confirmation_email(payload["email"], auth_token)

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "User has successfully registered",
                    "data": {
                        "user_uuid": userUUID,
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

class UserDetailView(UserView):
    def get(self, _, user_uuid):
        try:
            user = User.get_user_by_field(uuid=user_uuid)
            if user == None: raise NotFoundError("User not found")
  
            return JsonResponse({
                "status": "success",
                "data": user,
            })
        except Exception as e:
            return errorResponse(e)

class UserVerificationView(UserView):
    def get(self, _, auth_token):
        try:
            verificationParam = TokenManager.decode(auth_token)

            userUUID = User.confirm_user_email(verificationParam["user_uuid"])

            return JsonResponse({
                "status": "success",
                "message": "Email has successfully verified",
                "data": {
                    "user_uuid": userUUID,
                }
            })
        except Exception as e:
            return errorResponse(e)

class UserOAuthView(UserView):
    def get(self, _):
        authURI = OAuth.request_user_consent()

        return redirect(authURI)

class UserOAuthCallbackView(UserView):
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

            auth_token = TokenManager.encode({"user_uuid": userUUID.hex})
            send_confirmation_email(payload["email"], auth_token)

            return JsonResponse({
                "status": "success",
                "message": "OAuth success",
                "data": {
                    "user_uuid": userUUID,
                },
            })
        except Exception as e:
            return errorResponse(e)
