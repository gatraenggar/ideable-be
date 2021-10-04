# Generated by Django 3.2.6 on 2021-10-02 14:55

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0015_increase_story_task_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskAssignee',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('task_uuid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspaces.task')),
                ('workspace_member_uuid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspaces.workspacemember')),
            ],
            options={
                'db_table': '"task_assignees"',
            },
        ),
    ]