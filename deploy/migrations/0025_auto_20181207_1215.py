# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-07 04:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('deploy', '0024_auto_20181203_2121'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='credentials',
            name='passphrase',
        ),
        migrations.AlterField(
            model_name='credentials',
            name='private_key',
            field=models.TextField(default='', verbose_name='私钥'),
        ),
    ]
