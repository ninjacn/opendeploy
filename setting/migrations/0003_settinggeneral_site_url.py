# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-24 02:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('setting', '0002_auto_20181217_1401'),
    ]

    operations = [
        migrations.AddField(
            model_name='settinggeneral',
            name='site_url',
            field=models.CharField(default='', help_text='比如:http://opendeploy.test.com', max_length=255, verbose_name='站点域名'),
        ),
    ]