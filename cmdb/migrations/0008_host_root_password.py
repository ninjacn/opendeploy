# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-17 06:21
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmdb', '0007_auto_20181217_1414'),
    ]

    operations = [
        migrations.AddField(
            model_name='host',
            name='root_password',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='root密码'),
        ),
    ]
