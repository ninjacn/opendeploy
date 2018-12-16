# -*- coding: utf-8 -*-
from django.db import models

# Create your models here.

ALIYUN = 'aliyun'
QCLOUD = 'qcloud'
PUBLIC_CLOUD_CHOICES = (
    (ALIYUN, '阿里云'),
    (QCLOUD, '腾讯云'),
)

class Host(models.Model):
    STATUS_ENABLED = '1'
    STATUS_DISABLED = '0'
    STATUS_CHOICES = (
        (STATUS_ENABLED, '启用'),
        (STATUS_DISABLED, '禁用'),
    )
    ipaddr = models.CharField('IP地址', max_length=64,unique=True)
    hostname = models.CharField('主机名', max_length=255, unique=True, null=True, blank=True)
    comment = models.CharField('备注', max_length=255, default='')
    status = models.CharField(max_length=2, default=STATUS_ENABLED, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.ipaddr

    class Meta:
        db_table = 'cmdb_host'
        verbose_name_plural = '主机'
        verbose_name = '主机'

class HostGroup(models.Model):
    STATUS_ENABLED = '1'
    STATUS_DISABLED = '0'
    STATUS_CHOICES = (
        (STATUS_ENABLED, '启用'),
        (STATUS_DISABLED, '禁用'),
    )
    name = models.CharField(max_length=255,unique=True)
    host = models.ManyToManyField(Host)
    comment = models.CharField(max_length=255, default='')
    status = models.CharField(max_length=2, default=STATUS_ENABLED, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'cmdb_group'
        verbose_name_plural = '主机组'
        verbose_name = '主机组'
