# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-24
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.db import models

from common.models import TimeStampedModel

class Token(TimeStampedModel):
    title = models.CharField('Token说明', default='', max_length=255)
    token = models.CharField('Token', default='', max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'api_token'
        verbose_name_plural = 'Api Token'
        verbose_name = 'Api Token'
