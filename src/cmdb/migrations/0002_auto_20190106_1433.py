# -*- coding: utf-8 -*-
# Generated by Django 1.11.17 on 2019-01-06 06:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cmdb', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='host',
            name='hostname',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='主机名'),
        ),
    ]
