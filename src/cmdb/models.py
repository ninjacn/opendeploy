# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.db import models

from common.models import TimeStampedModel

ALIYUN = 'aliyun'
QCLOUD = 'qcloud'
PUBLIC_CLOUD_CHOICES = (
    (ALIYUN, '阿里云'),
    (QCLOUD, '腾讯云'),
)

class Host(TimeStampedModel):
    STATUS_ENABLED = '1'
    STATUS_DISABLED = '0'
    STATUS_CHOICES = (
        (STATUS_ENABLED, '启用'),
        (STATUS_DISABLED, '禁用'),
    )
    PROVIDER_OWN = 'own_idc'
    PROVIDER_CHOICES = (
        (PROVIDER_OWN, '自有IDC'),
        (ALIYUN, '阿里云'),
        (QCLOUD, '腾讯云'),
    )
    ipaddr = models.CharField('IP地址', max_length=64,unique=True)
    hostname = models.CharField('主机名', max_length=255, null=True, blank=True)
    root_password = models.CharField('root密码', max_length=255, null=True, blank=True)
    provider = models.CharField('服务商', max_length=16, default=PROVIDER_OWN, choices=PROVIDER_CHOICES)
    instance_id = models.CharField('InstanceId', max_length=255, blank=True, null=True)
    comment = models.CharField('备注', max_length=255, default='')
    status = models.CharField(max_length=2, default=STATUS_ENABLED, choices=STATUS_CHOICES)

    def __str__(self):
        return self.ipaddr

    class Meta:
        db_table = 'cmdb_host'
        verbose_name_plural = '主机'
        verbose_name = '主机'

class HostGroup(TimeStampedModel):
    STATUS_ENABLED = '1'
    STATUS_DISABLED = '0'
    STATUS_CHOICES = (
        (STATUS_ENABLED, '启用'),
        (STATUS_DISABLED, '禁用'),
    )
    name = models.CharField(max_length=255,unique=True)
    host = models.ManyToManyField(Host)
    comment = models.CharField(max_length=255, default='', null=True, blank=True)
    status = models.CharField(max_length=2, default=STATUS_ENABLED, choices=STATUS_CHOICES)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'cmdb_group'
        verbose_name_plural = '主机组'
        verbose_name = '主机组'
