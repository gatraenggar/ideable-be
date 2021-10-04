from .models import User
from .utils.model_mapper import ModelMapper
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt
import sys

sys.path.append("..")
from errors.client_error import NotFoundError
from errors.handler import errorResponse

class UserView(generic.ListView):
    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, _):
        userModels = User.objects.all().values()
        users = ModelMapper.to_user_list(userModels)

        return JsonResponse(
            status = 200,
            data = {
                "status": "success",
                "data": users
            }
        )

class UserDetailView(UserView):
    def get(self, _, user_uuid):
        try:
            user = User.get_user_by_fields(uuid=user_uuid)
            if user == None: raise NotFoundError("User not found")
  
            return JsonResponse(
                status = 200,
                data = {
                    "status": "success",
                    "data": user,
                }
            )
        except Exception as e:
            return errorResponse(e)
