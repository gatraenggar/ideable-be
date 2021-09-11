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

    def get_refresh_token(token):
        authModel = Authentications.objects.filter(refresh_token=token).values()
        if len(authModel) != 1: return None

        return authModel[0]["refresh_token"]

    def delete_refresh_token(token):
        result = Authentications.objects.filter(refresh_token=token).delete()

        return result[0]
