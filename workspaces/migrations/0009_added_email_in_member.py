# Generated by Django 3.2.6 on 2021-09-27 12:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0008_transform_queue_model'),
    ]

    operations = [
        migrations.AddField(
            model_name='workspacemember',
            name='email',
            field=models.EmailField(max_length=254, null=True, unique=True),
        ),
    ]