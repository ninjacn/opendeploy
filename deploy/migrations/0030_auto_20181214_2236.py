# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-14 14:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploy', '0029_auto_20181214_2235'),
    ]

    operations = [
        migrations.AlterField(
            model_name='credentials',
            name='type',
            field=models.IntegerField(choices=[(1, '用户名和密码'), (2, '用户名和私钥')], default=1),
        ),
    ]