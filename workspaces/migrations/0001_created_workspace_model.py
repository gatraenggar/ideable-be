# Generated by Django 3.2.6 on 2021-09-12 04:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0003_added_is_oauth'),
    ]

    operations = [
        migrations.CreateModel(
            name='Workspace',
            fields=[
                ('uuid', models.UUIDField(auto_created=True, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=32)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.DO_NOTHING, to='users.user')),
            ],
            options={
                'db_table': '"workspaces"',
            },
        ),
    ]
