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

