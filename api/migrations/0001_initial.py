# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-12-24 02:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Token',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(default='', max_length=255, verbose_name='Token说明')),
                ('token', models.CharField(default='', max_length=255, verbose_name='Token')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
            ],
            options={
                'verbose_name': 'Api Token',
                'verbose_name_plural': 'Api Token',
                'db_table': 'api_token',
            },
        ),
    ]
