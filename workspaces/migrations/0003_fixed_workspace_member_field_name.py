# Generated by Django 3.2.6 on 2021-09-13 06:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0002_created_workspace_member'),
    ]

    operations = [
        migrations.RenameField(
            model_name='workspacemember',
            old_name='member_id',
            new_name='member',
        ),
        migrations.RenameField(
            model_name='workspacemember',
            old_name='workspace_id',
            new_name='workspace',
        ),
    ]
