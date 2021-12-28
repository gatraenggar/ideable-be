from .models import Authentication
from .utils.password_manager import PasswordManager
from .utils.token_manager import TokenManager
from .validators import OAuthSignForm, RegistrationForm, LoginForm, ResendEmailForm
from .services.rabbitmq.email_confirmation import send_confirmation_email
from .services.oauth.oauth import OAuth
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import json, jwt, sys, uuid

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

            registeredUser = User.objects.filter(email=payload["email"]).values("email")
            if len(registeredUser): raise ConflictError("Email already registered")

            payload["password"] = PasswordManager.hash(payload["password"])
            user = User(**payload)
            user.save()

            userUUID = user.uuid
            emailAuthToken = TokenManager.generate_random_token({ "user_uuid": userUUID.hex })
            send_confirmation_email(payload["email"], emailAuthToken)

            accessToken = TokenManager.generate_access_token(userUUID.hex)
            refreshToken = TokenManager.generate_refresh_token(userUUID.hex)

            Authentication(refreshToken).save()

            response = JsonResponse(
                status = 201,
                data = {
                    "status": "success",
                    "message": "User has successfully registered",
                    "data": {
                        "first_name": payload["first_name"],
                        "last_name": payload["last_name"],
                        "is_confirmed": False,
                    }
                }
            )

            response.set_cookie(
                key="access_token",
                value=accessToken,
                max_age=None,
                expires=None,
                httponly=True
            )
            response.set_cookie(
                key="refresh_token",
                value=refreshToken,
                max_age=None,
                expires=None,
                httponly=True
            )

            return response
        except Exception as e:
            return errorResponse(e)

class EmailVerificationView(AuthView):
    def get(self, _, auth_token):
        try:
            tokenParam = TokenManager.verify_random_token(auth_token)

            user = User.objects.get(uuid=tokenParam["user_uuid"])
            if user.is_confirmed: raise ClientError("Request is no longer valid")

            user.is_confirmed = True
            user.save(update_fields=["is_confirmed"])

            accessToken = TokenManager.generate_access_token(tokenParam["user_uuid"])
            refreshToken = TokenManager.generate_refresh_token(tokenParam["user_uuid"])

            Authentication(refreshToken).save()

            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Email has successfully verified",
                }
            )
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
            emailAuthToken = TokenManager.generate_random_token({ "user_uuid": userData["user_uuid"] })

            send_confirmation_email(payload["email"], emailAuthToken)

            return JsonResponse(
                status = 202,
                data = {
                    "status": "success",
                    "message": "An email verification has successfully re-sent",
                }
            )
        except Exception as e:
            return errorResponse(e)

class OAuthView(AuthView):
    def get(self, _):
        try:
            authURI = OAuth.request_user_consent()

            return redirect(authURI)

        except Exception as e:
            return errorResponse(e)

class OAuthCallbackView(AuthView):
    def get(self, request):
        try:
            authCode = request.GET.get("code")
            userInfo = OAuth.request_user_info(authCode)

            payload = {
                "email": userInfo["email"],
                "first_name": userInfo["given_name"] if "given_name" in userInfo else "",
                "last_name": userInfo["family_name"] if "family_name" in userInfo else "",
                "is_oauth": True,
            }

            userUUID = None
            statusCode = None

            registeredUser = User.objects.filter(email=payload["email"]).values("uuid", "is_oauth")
            if not len(registeredUser): 
                user = User(**payload)
                user.save()

                statusCode = 201
                userUUID = user.uuid

                emailAuthToken = TokenManager.generate_random_token({ "user_uuid": userUUID.hex })
                send_confirmation_email(payload["email"], emailAuthToken)
            else:
                if registeredUser[0]["is_oauth"]:
                    userUUID = registeredUser[0]["uuid"]
                    statusCode = 200
                else: raise ConflictError("Email already registered")

            accessToken = TokenManager.generate_access_token(userUUID.hex)
            refreshToken = TokenManager.generate_refresh_token(userUUID.hex)

            Authentication(refreshToken).save()

            return JsonResponse(
                status = statusCode,
                data = {
                    "status": "success",
                    "message": "OAuth success",
                    "data": {
                        "access_token": accessToken,
                        "refresh_token": refreshToken,
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

            userUUID = None
            statusCode = None

            registeredUsers = User.objects.filter(email=payload["email"]).values("uuid", "is_oauth", "is_confirmed")
            if not len(registeredUsers): 
                user = User(**payload)
                user.save()

                statusCode = 201
                userUUID = user.uuid

                emailAuthToken = TokenManager.generate_random_token({ "user_uuid": userUUID.hex })
                send_confirmation_email(payload["email"], emailAuthToken)
            else:
                if registeredUsers[0]["is_oauth"]:
                    userUUID = registeredUsers[0]["uuid"]
                    statusCode = 200
                else: raise ConflictError("Email already registered")

            accessToken = TokenManager.generate_access_token(userUUID.hex)
            refreshToken = TokenManager.generate_refresh_token(userUUID.hex)

            Authentication(refreshToken).save()

            response = JsonResponse(
                status = statusCode,
                data = {
                    "status": "success",
                    "message": "OAuth success",
                    "data": {
                        "first_name": payload["first_name"],
                        "last_name": payload["last_name"],
                        "is_confirmed": registeredUsers[0]["is_confirmed"] if len(registeredUsers) == 1 else False,
                    }
                }
            )

            response.set_cookie(
                key="access_token",
                value=accessToken,
                max_age=None,
                expires=None,
                httponly=True
            )
            response.set_cookie(
                key="refresh_token",
                value=refreshToken,
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

            users = User.objects.filter(email=payload["email"]).values(
                "uuid",
                "password",
                "first_name",
                "last_name",
                "is_oauth",
                "is_confirmed"
            )
            if len(users) != 1 or users[0]["is_oauth"]: raise AuthenticationError("Email or password doesn't match any account")

            user = users[0]
            isPasswordTrue = PasswordManager.verify(user["password"], payload["password"])
            if not isPasswordTrue: raise AuthenticationError("Email or password doesn't match any account")

            accessToken = TokenManager.generate_access_token(user["uuid"].hex)
            refreshToken = TokenManager.generate_refresh_token(user["uuid"].hex)

            Authentication(refreshToken).save()

            response = JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Login success",
                    "data": {
                        "first_name": user["first_name"],
                        "last_name": user["last_name"],
                        "is_confirmed": user["is_confirmed"],
                    }
                }
            )

            response.set_cookie(
                key="access_token",
                value=accessToken,
                max_age=None,
                expires=None,
                httponly=True
            )
            response.set_cookie(
                key="refresh_token",
                value=refreshToken,
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
            isDeleted = Authentication.objects.filter(refresh_token=refreshToken).delete()[0]
            if not isDeleted: raise NotFoundError("Token not found")

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

            userData = None
            try: 
                userData = TokenManager.verify_refresh_token(refreshToken)
            except Exception as e:
                if isinstance(e, (jwt.ExpiredSignatureError)): raise AuthenticationError('Re-login required')
                raise e

            refreshToken = Authentication.objects.filter(refresh_token=refreshToken).values()
            if refreshToken == None: raise NotFoundError("Refresh token not found")            

            userUUID = uuid.UUID(userData["user_uuid"])
            accessToken = TokenManager.generate_access_token(userUUID.hex)

            response = JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "message": "Access token has successfully generated",
                }
            )

            response.set_cookie(
                key="access_token",
                value=accessToken,
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
