# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.db import models
from django.contrib.auth.models import User

from common.models import TimeStampedModel

class UserDetail(TimeStampedModel):
    TYPE_LDAP = 'ldap'
    TYPE_LOCAL = 'local'
    TYPE_CHOICES = (
        (TYPE_LDAP, 'LDAP账号'),
        (TYPE_LOCAL, '本地账号'),
    )
    type = models.CharField(max_length=10, default=TYPE_LOCAL, choices=TYPE_CHOICES)
    username = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, unique=True)
    dingding = models.CharField('dingding',max_length=64, default='', help_text='', null=True)
    ldap_dn = models.CharField('ldap_dn',max_length=1024, default='', help_text='', null=True)

    class Meta:
        db_table = 'accounts_user_detail'
        verbose_name_plural = '用户附加表'
        verbose_name = '用户附加表'
