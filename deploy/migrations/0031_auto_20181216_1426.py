# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-16 06:26
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('deploy', '0030_auto_20181214_2236'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Setting',
        ),
        migrations.DeleteModel(
            name='SettingLdap',
        ),
        migrations.DeleteModel(
            name='SettingMail',
        ),
    ]