# -*- coding: utf-8 -*-
# Author: Pengming Yao<x@ninjacn.com>
# Date created: 2018-12-16

import json

from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse 
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test

from admin.forms import AddHostForm, AddHostGroupForm, EditHostGroupForm, \
        ImportFromPublicCloudForm
from deploy.models import Env
from cmdb.models import Host, HostGroup, PUBLIC_CLOUD_CHOICES, ALIYUN, QCLOUD
from setting.services import SettingService
from cmdb.services import QcloudService, AliyunService
from cmdb.models import Host, ALIYUN, QCLOUD

# Create your views here.

@user_passes_test(lambda u: u.is_superuser)
def host(request):
    hosts = Host.objects.all()
    return render(request, 'admin/cmdb/host.html', {
        "hosts": hosts,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def host_add(request):
    if request.method== 'POST':
        f = AddHostForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                host = Host()
                host.ipaddr = cleaned_data['ipaddr']
                host.hostname = cleaned_data['hostname']
                host.status = cleaned_data['status']
                host.comment = cleaned_data['comment']
                host.save()
            finally:
                return redirect('/admin/cmdb/host')
    else:
        f = AddHostForm()
    return render(request, 'admin/cmdb/add_host.html', {
        "form": f,
        "status_choices": Host.STATUS_CHOICES,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def host_edit(request, id):
    host = Host.objects.get(id=id)
    if request.method== 'POST':
        f = AddHostForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                host.ipaddr = cleaned_data['ipaddr']
                host.hostname = cleaned_data['hostname']
                host.status = cleaned_data['status']
                host.comment = cleaned_data['comment']
                host.save()
            finally:
                return redirect('/admin/cmdb/host')
    else:
        f = AddHostForm()
    return render(request, 'admin/cmdb/edit_host.html', {
        "form": f,
        "host": host,
        "status_choices": Host.STATUS_CHOICES,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def hostgroup(request):
    data = {}
    hostGroup = HostGroup.objects.all()
    for item in hostGroup:
        data['id'] = item.id
        data['name'] = item.name
        data['comment'] = item.comment
        data['created_at'] = item.created_at
        data['updated_at'] = item.updated_at
        data['host'] = item.host.all()
    return render(request, 'admin/cmdb/hostgroup.html', {
        "data": data,
        "hostGroup": hostGroup,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def hostgroup_add(request):
    if request.method== 'POST':
        f = AddHostGroupForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                hostGroup = HostGroup()
                hostGroup.name = cleaned_data['name']
                hostGroup.comment = cleaned_data['comment']
                hostGroup.status = cleaned_data['status']
                hostGroup.save()

                hosts = request.POST.getlist('hosts')
                if hosts:
                    for id in hosts:
                        hostGroup.host.add(Host.objects.get(pk=id))
            finally:
                return redirect('/admin/cmdb/hostgroup')
    else:
        f = AddHostGroupForm()
    return render(request, 'admin/cmdb/add_hostgroup.html', {
        "form": f,
        "hosts": Host.objects.filter(status=Host.STATUS_ENABLED),
        "status_choices": HostGroup.STATUS_CHOICES,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def hostgroup_edit(request, gid):
    hostgroup = HostGroup.objects.get(id=gid)
    if request.method== 'POST':
        f = EditHostGroupForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                hostgroup.name = cleaned_data['name']
                hostgroup.comment = cleaned_data['comment']
                hostgroup.status = cleaned_data['status']
                hostgroup.save()

                hostgroup.host.clear()
                hosts = request.POST.getlist('hosts')
                if hosts:
                    for id in hosts:
                        hostgroup.host.add(Host.objects.get(pk=id))
            finally:
                return redirect('/admin/cmdb/hostgroup')
    else:
        f = EditHostGroupForm()
    return render(request, 'admin/cmdb/edit_hostgroup.html', {
        "form": f,
        "hostgroup": hostgroup,
        "hosts": Host.objects.filter(status=Host.STATUS_ENABLED),
        "status_choices": HostGroup.STATUS_CHOICES,
    })

@user_passes_test(lambda u: u.is_superuser)
def import_from_public_cloud(request):
    if request.method== 'POST':
        f = ImportFromPublicCloudForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                pass
            finally:
                return redirect('admin:cmdb.host')
    else:
        f = ImportFromPublicCloudForm()
    return render(request, 'admin/cmdb/import_from_public_cloud.html', {
        "form": f,
        "public_cloud_choices": PUBLIC_CLOUD_CHOICES,
        })

@user_passes_test(lambda u: u.is_superuser)
def get_region_list(request):
    provider = request.GET.get('provider')
    settingService = SettingService()
    auth_info = settingService.get_public_cloud_info()
    res = []
    if provider == ALIYUN:
        aliyun = AliyunService(auth_info.aliyun_access_key_id, auth_info.aliyun_access_key_secret)
        json_data = json.loads(aliyun.get_all_region())
        try:
            regions = json_data['Regions']['Region']
            if regions:
                for region in regions:
                    tmp = {}
                    tmp['id'] = region['RegionId']
                    tmp['name'] = region['LocalName']
                    res.append(tmp)
        except:
            pass
    elif provider == QCLOUD:
        qcloud = QcloudService(auth_info.qcloud_secret_id, auth_info.qcloud_secret_key)
        json_data = json.loads(qcloud.get_all_region())
        try:
            regions = json_data['RegionSet']
            if regions:
                for region in regions:
                    tmp = {}
                    tmp['id'] = region['Region']
                    tmp['name'] = region['RegionName']
                    res.append(tmp)
        except:
            pass
    else:
        pass
    return JsonResponse(res, safe=False)

@user_passes_test(lambda u: u.is_superuser)
def import_from_public_cloud_as_api(request):
    provider = request.GET.get('provider')
    region = request.GET.get('region')
    settingService = SettingService()
    auth_info = settingService.get_public_cloud_info()
    count = 0
    vps_list = []
    if provider == ALIYUN:
        aliyun = AliyunService(auth_info.aliyun_access_key_id, auth_info.aliyun_access_key_secret)
        json_data = json.loads(aliyun.get_allhost(region))
        if ('TotalCount' in json_data) and (json_data['TotalCount'] > 0):
            instances = json_data['Instances']['Instance']
            for item in instances:
                try:
                    ipaddr = item['VpcAttributes']['PrivateIpAddress']['IpAddress'][0]
                except:
                    continue

                try:
                    host = Host.objects.get(ipaddr=ipaddr)
                    host.hostname = item['HostName']
                    host.comment = item['Description']
                    if item['Status'] == 'Running':
                        host.status = Host.STATUS_ENABLED
                    else:
                        host.status = Host.STATUS_DISABLED
                    host.save()
                except:
                    host = Host()
                    host.provider = ALIYUN
                    host.ipaddr = ipaddr
                    host.hostname = item['HostName']
                    host.instance_id = item['InstanceId']
                    host.comment = item['Description']
                    if item['Status'] == 'Running':
                        host.status = Host.STATUS_ENABLED
                    else:
                        host.status = Host.STATUS_DISABLED
                    host.save()
                finally:
                    count += 1
                    vps_list.append(ipaddr + '-' + item['HostName'])

    elif provider == QCLOUD:
        qcloud = QcloudService(auth_info.qcloud_secret_id, auth_info.qcloud_secret_key)
        try:
            json_data = json.loads(qcloud.get_allhost(region))
            if ('TotalCount' in json_data) and (json_data['TotalCount'] > 0):
                instances = json_data['InstanceSet']
                for item in instances:
                    try:
                        ipaddr = item['PrivateIpAddresses'][0]
                    except:
                        continue

                    try:
                        host = Host.objects.get(ipaddr=ipaddr)
                        host.hostname = item['InstanceName']
                        host.save()
                    except:
                        host = Host()
                        host.provider = QCLOUD
                        host.ipaddr = ipaddr
                        host.hostname = item['InstanceName']
                        host.instance_id = item['InstanceId']
                        host.status = Host.STATUS_ENABLED
                        host.save()
                    finally:
                        count += 1
                        vps_list.append(ipaddr + '-' + item['InstanceName'])
        except:
            pass
    else:
        pass
    res = {'count':count, 'vps_list':vps_list}
    return JsonResponse(res, safe=False)
