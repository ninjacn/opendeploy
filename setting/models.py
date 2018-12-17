# -*- coding: utf-8 -*-
# Author: Pengming Yao<x@ninjacn.com>
# Date created: 2018-12-16

from django.db import models

# 通用
class SettingGeneral(models.Model):
    enable_register = models.BooleanField('开启用户注册', default=True)

    def __str__(self):
        return 'setting_general'

    class Meta:
        db_table = 'setting_general'
        verbose_name_plural = '设置 - 通用'
        verbose_name = '设置 - 通用'

class SettingMail(models.Model):
    from_email = models.CharField('发送人', max_length=255, default='', help_text='例: opendeploy@ninjacn.com或Opendeploy<opendeploy@ninjacn.com>')
    host = models.CharField('SMTP主机', max_length=255, default='', help_text='例: smtp.exmail.qq.com')
    port = models.CharField('端口', max_length=255, default='25', help_text='25')
    username = models.CharField('发送人账号', max_length=255, default='')
    password = models.CharField('发送人密码', max_length=255, default='', blank=True)
    use_tls = models.BooleanField('TLS', default=False)

    def __str__(self):
        return self.from_email

    class Meta:
        db_table = 'setting_mail'
        verbose_name_plural = '设置 - 邮箱'
        verbose_name = '设置 - 邮箱'

class SettingLdap(models.Model):
    host = models.CharField('发送人', max_length=255, default='')
    port = models.CharField('发送人', max_length=255, default='389')
    uid = models.CharField('uid', max_length=255, default='uid')
    base = models.CharField('base', max_length=255, default='uid')
    bind_dn = models.CharField('bind_dn', max_length=255, default='')
    password = models.CharField('密码', max_length=255, default='')
    enable = models.BooleanField('启用', default=False)

    def __str__(self):
        return self.from_email

    class Meta:
        db_table = 'setting_ldap'
        verbose_name_plural = '设置 - LDAP'
        verbose_name = '设置 - LDAP'

class SettingPublicCloud(models.Model):
    aliyun_access_key_id = models.CharField('阿里云-AccessKeyID', max_length=255, default='', blank=True)
    aliyun_access_key_secret = models.CharField('阿里云-AccessKeySecret', max_length=255, default='', blank=True)
    qcloud_secret_id = models.CharField('腾讯云-SecretId', max_length=255, default='', blank=True)
    qcloud_secret_key = models.CharField('腾讯云-SecretKey', max_length=255, default='', blank=True)

    def __str__(self):
        return 'public_cloud' + str(self.id)

    class Meta:
        db_table = 'setting_public_cloud'
        verbose_name_plural = '设置 - 公有云'
        verbose_name = '设置 - 公有云'
