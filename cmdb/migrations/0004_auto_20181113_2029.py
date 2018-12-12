# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-11-13 12:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmdb', '0003_auto_20181113_0550'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='comment',
            field=models.CharField(default='', max_length=255, verbose_name='备注'),
        ),
        migrations.AlterField(
            model_name='host',
            name='hostname',
            field=models.CharField(blank=True, max_length=255, null=True, unique=True, verbose_name='主机名'),
        ),
        migrations.AlterField(
            model_name='host',
            name='ipaddr',
            field=models.CharField(max_length=64, unique=True, verbose_name='IP地址'),
        ),
    ]
