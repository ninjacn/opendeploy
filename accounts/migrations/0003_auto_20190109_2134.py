# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-01-09 13:34
from __future__ import unicode_literals

from django.db import migrations
from django.contrib.auth.models import User

def load_accounts(apps, schema_editor):
    try:
        raw_password = ''
        user = User()
        user.username = 'git_robot'
        user.first_name = 'Git机器人'
        user.is_active = 1
        user.is_staff = 0
        user.is_superuser = 0
        user.set_password(raw_password)
        user.save()
    except:
        pass

def delete_accounts(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.get(username='git_robot').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20190105_2353'),
    ]

    operations = [
        migrations.RunPython(load_accounts, delete_accounts),
    ]
