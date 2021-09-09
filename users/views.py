from .models import User
from .utils.password_hasher import Hasher
from .utils.model_mapper import ModelMapper
from .utils.token_manager import TokenManager
from .validators import RegistrationForm
from .services.rabbitmq.email_confirmation import send_confirmation_email
from django.http import JsonResponse
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
        userModels = User.objects.all().values()
        users = ModelMapper.to_user_list(userModels)

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

            registeredUser = User.objects.filter(email=payload["email"])
            if len(registeredUser): raise ConflictError("Email already registered")

            User(
                email=payload["email"],
                password=Hasher.hash_password(payload["password"]),
                first_name=payload["first_name"],
                last_name=payload["last_name"]
            ).save()

            user = User.objects.filter(email=payload["email"]).values()[0]

            auth_token = TokenManager.encode({"user_uuid": user["uuid"].hex})
            send_confirmation_email(user["email"], auth_token)

            return JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "User has successfully registered",
                    "data": {
                        "user_uuid": user["uuid"]
                    }
                }
            )
        except Exception as e:
            return errorResponse(e)

class UserDetailView(UserView):
    def get(self, _, user_uuid):
        try:
            userModel = User.objects.filter(pk=user_uuid).values()
            if len(userModel) != 1: raise NotFoundError("User not found")

            user = ModelMapper.to_single_user(userModel)
    
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

            user = User.objects.get(uuid=verificationParam["user_uuid"])
            if user.is_confirmed: raise ClientError("Request is no longer valid")

            user.is_confirmed = True
            user.save(update_fields=['is_confirmed'])

            return JsonResponse({
                "status": "success",
                "message": "Email has successfully verified",
                "data": {
                    "user_uuid": user.uuid,
                }
            })
        except Exception as e:
            return errorResponse(e)
