# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-01-01 07:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmdb', '0008_host_root_password'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hostgroup',
            name='comment',
            field=models.CharField(blank=True, default='', max_length=255, null=True),
        ),
    ]