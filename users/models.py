from django.db import models
from .utils.model_mapper import ModelMapper
import json, sys, uuid

sys.path.append("..")
from errors.client_error import ClientError

class User(models.Model):
    class Meta:
        db_table = '"users"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=254)
    password = models.CharField(max_length=254)
    first_name = models.CharField(max_length=20)
    last_name = models.CharField(max_length=20)
    is_oauth = models.BooleanField(default=False, editable=False)
    is_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return json.dumps({
            "uuid": self.uuid,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "is_oauth": self.is_oauth,
            "is_confirmed": self.is_confirmed,
            "created_at": self.created_at,
        })

    def register_user(payload):
        User(**payload).save()

        user = User.objects.filter(email=payload["email"]).values()[0]

        return user["uuid"]

    def get_users():
        userModels = User.objects.all().values()

        users = ModelMapper.to_user_list(userModels)

        return users

    def get_user_by_fields(**payload):
        userModel = User.objects.filter(**payload).values()
        if not len(userModel): return None

        user = ModelMapper.to_single_user(userModel)

        return user

    def get_user_model_by_fields(**payload):
        userModel = User.objects.filter(**payload).values()
        if len(userModel) != 1: return None

        return userModel[0]

    def confirm_user_email(user_uuid):
        user = User.objects.get(uuid=user_uuid)
        if user.is_confirmed: raise ClientError("Request is no longer valid")

        user.is_confirmed = True
        user.save(update_fields=["is_confirmed"])

        return user_uuid
