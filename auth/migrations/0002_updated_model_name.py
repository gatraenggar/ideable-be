# Generated by Django 3.2.6 on 2021-09-12 04:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_created_authentications_table'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Authentications',
            new_name='Authentication',
        ),
    ]