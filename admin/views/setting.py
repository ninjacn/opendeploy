# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from admin.forms import  SettingGeneralForm, SettingMailForm, SettingPublicCloudForm, \
        SettingLdapForm
from setting.models import SettingMail, SettingGeneral, SettingPublicCloud, \
        SettingLdap
from setting.services import SettingService
from accounts.services import LdapService
from common.views import get_common_response_by_api

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def general(request):
    settingService = SettingService()
    general_info = settingService.get_general_info()
    if request.method== 'POST':
        f = SettingGeneralForm(request.POST)
        if f.is_valid():
            try:
                cleaned_data = f.cleaned_data
                SettingGeneral.objects.all().delete()
                setting = SettingGeneral()
                setting.enable_register = cleaned_data['enable_register']
                setting.site_url = cleaned_data['site_url']
                setting.save()
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('admin:setting.general')
    else:
        f = SettingGeneralForm()
    return render(request, 'admin/setting/general.html', {
        "form": f,
        "general_info": general_info,
        })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def mail(request):
    settingService = SettingService()
    mail_info = settingService.get_mail_info()
    if request.method== 'POST':
        f = SettingMailForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                SettingMail.objects.all().delete()
                settingMail = SettingMail()
                settingMail.from_email = cleaned_data['from_email']
                settingMail.host = cleaned_data['host']
                settingMail.port = cleaned_data['port']
                settingMail.username = cleaned_data['username']
                settingMail.password = cleaned_data['password']
                settingMail.use_tls = cleaned_data['use_tls']
                settingMail.save()
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('admin:setting.mail')
    else:
        f = SettingMailForm()
    return render(request, 'admin/setting/mail.html', {
        "form": f,
        "mail_info": mail_info,
        })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def public_cloud(request):
    settingService = SettingService()
    info = settingService.get_public_cloud_info()
    if request.method== 'POST':
        f = SettingPublicCloudForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                SettingPublicCloud.objects.all().delete()
                settingPublicCloud = SettingPublicCloud()
                settingPublicCloud.aliyun_access_key_id = cleaned_data['aliyun_access_key_id']
                settingPublicCloud.aliyun_access_key_secret = cleaned_data['aliyun_access_key_secret']
                settingPublicCloud.qcloud_secret_id = cleaned_data['qcloud_secret_id']
                settingPublicCloud.qcloud_secret_key = cleaned_data['qcloud_secret_key']
                settingPublicCloud.save()
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('admin:setting.public_cloud')
    else:
        f = SettingPublicCloudForm()
    return render(request, 'admin/setting/public_cloud.html', {
        "form": f,
        "info": info,
        })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def ldap(request):
    settingService = SettingService()
    ldap_info = settingService.get_ldap_info()
    if request.method== 'POST':
        f = SettingLdapForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                SettingLdap.objects.all().delete()
                settingLdap = SettingLdap()
                settingLdap.host = cleaned_data['host']
                settingLdap.port = cleaned_data['port']
                settingLdap.uid = cleaned_data['uid']
                settingLdap.base = cleaned_data['base']
                settingLdap.bind_dn = cleaned_data['bind_dn']
                settingLdap.password = cleaned_data['password']
                settingLdap.enable = cleaned_data['enable']
                settingLdap.save()
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('admin:setting.ldap')
    else:
        f = SettingLdapForm()
    return render(request, 'admin/setting/ldap.html', {
        "form": f,
        "ldap_info": ldap_info,
        })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def check_ldap_account_valid(request):
    res = get_common_response_by_api()
    ldapService = LdapService()
    if ldapService.check_account_valid():
        res['msg'] = '账号检测成功'
    else:
        if ldapService.error_msg:
            res['msg'] = '账号检测异常 - ' + ldapService.error_msg
        else:
            res['msg'] = '账号检测异常'
        res['error_code'] = 1
    return JsonResponse(res)
