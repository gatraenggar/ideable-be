# Generated by Django 3.2.6 on 2021-10-01 08:03

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0012_created_story_model'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='story',
            name='id',
        ),
        migrations.AddField(
            model_name='story',
            name='desc',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.AddField(
            model_name='story',
            name='name',
            field=models.CharField(max_length=32, null=True),
        ),
        migrations.AddField(
            model_name='story',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
    ]
