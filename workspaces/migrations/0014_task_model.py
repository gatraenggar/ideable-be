# Generated by Django 3.2.6 on 2021-10-02 12:22

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('workspaces', '0013_added_story_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Task',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=32, null=True)),
                ('desc', models.CharField(blank=True, max_length=500, null=True)),
                ('priority', models.IntegerField(choices=[(1, 'Low'), (2, 'Medium'), (3, 'High')], default=1)),
                ('status', models.IntegerField(choices=[(1, 'Todo'), (2, 'In Progress'), (3, 'In Review'), (4, 'In Evaluation'), (5, 'Done')], default=1)),
                ('story_uuid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='workspaces.story')),
            ],
            options={
                'db_table': '"tasks"',
            },
        ),
    ]
