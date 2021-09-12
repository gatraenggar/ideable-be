from django.db import models
import json, sys, uuid

sys.path.append("..")
from users.models import User

class Workspace(models.Model):
    class Meta:
        db_table = '"workspaces"'

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=32)
    owner = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return json.dumps({
            "uuid": self.uuid,
            "name": self.name,
            "owner": self.owner,
        })