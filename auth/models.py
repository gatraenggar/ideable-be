from django.db import models
import json

class Authentications(models.Model):
    class Meta:
        db_table = '"authentications"'

    refresh_token = models.CharField(primary_key=True, max_length=1000)

    def __str__(self):
        return json.dumps({
            "refresh_token": self.refresh_token,
        })
