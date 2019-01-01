# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import json

from django.contrib import messages
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.template.response import TemplateResponse 
from django.db import transaction
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from opendeploy import settings
from admin.forms import AddHostForm, AddHostGroupForm, EditHostGroupForm, \
        ImportFromPublicCloudForm, HostGroupForm
from deploy.models import Env
from cmdb.models import Host, HostGroup, PUBLIC_CLOUD_CHOICES, ALIYUN, QCLOUD
from setting.services import SettingService
from cmdb.services import QcloudService, AliyunService
from cmdb.models import Host, ALIYUN, QCLOUD

# Create your views here.

@user_passes_test(lambda u: u.is_superuser)
def host(request):
    q = request.GET.get('q')
    if q:
        hosts = Host.objects.filter(Q(ipaddr__contains=q) | Q(hostname__contains=q))
    else:
        hosts = Host.objects.all()
    paginator = Paginator(hosts, settings.PAGE_SIZE)
    page = request.GET.get('page')
    if not page:
        page = 1
    try:
        hosts = paginator.page(page)
    except PageNotAnInteger:
        hosts = paginator.page(1)
    except EmptyPage:
        hosts = paginator.page(paginator.num_pages)

    get_copy = request.GET.copy()
    parameters = get_copy.pop('page', True) and get_copy.urlencode()
    return render(request, 'admin/cmdb/host.html', {
        "hosts": hosts,
        'parameters': parameters,
        'q': q,
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
                host.provider = cleaned_data['provider']
                host.root_password = cleaned_data['root_password']
                host.hostname = cleaned_data['hostname']
                host.status = cleaned_data['status']
                host.comment = cleaned_data['comment']
                host.save()
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('/admin/cmdb/host')
    else:
        f = AddHostForm()
    return render(request, 'admin/cmdb/add_host.html', {
        "form": f,
        "status_choices": Host.STATUS_CHOICES,
        "provider_choices": Host.PROVIDER_CHOICES,
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
                host.provider = cleaned_data['provider']
                host.root_password = cleaned_data['root_password']
                host.hostname = cleaned_data['hostname']
                host.status = cleaned_data['status']
                host.comment = cleaned_data['comment']
                host.save()
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('admin:cmdb.host')
    else:
        f = AddHostForm()
    return render(request, 'admin/cmdb/edit_host.html', {
        "form": f,
        "host": host,
        "status_choices": Host.STATUS_CHOICES,
        "provider_choices": Host.PROVIDER_CHOICES,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def host_del(request, id):
    try:
        host = Host.objects.get(id=id)
        host.delete()
        messages.info(request, '删除成功')
    except:
        messages.error(request, '删除失败')
    return redirect('admin:cmdb.host')

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
        f = HostGroupForm()
    return TemplateResponse(request, 'admin/cmdb/add_hostgroup.html', {
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
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('/admin/cmdb/hostgroup')
    else:
        f = EditHostGroupForm()

    def rebuild_hosts(host):
        tmp = {}
        tmp['id'] = host.id
        tmp['hostname'] = host.hostname
        tmp['ipaddr'] = host.ipaddr
        return tmp

    hosts_render = []
    hosts = Host.objects.filter(status=Host.STATUS_ENABLED)
    hosts_render=map(rebuild_hosts, hosts)
    return render(request, 'admin/cmdb/edit_hostgroup.html', {
        "form": f,
        "hostgroup": hostgroup,
        "hosts": hosts_render,
        "status_choices": HostGroup.STATUS_CHOICES,
    })

@transaction.atomic
def hostgroup_del(request, id):
    try:
        hostGroup = HostGroup.objects.get(id=id)
        hostGroup.delete()
        messages.info(request, '删除成功')
    except:
        messages.error(request, '删除失败')
    return redirect('admin:cmdb.hostgroup')

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
        page = 1
        while page < 100:
            json_data = json.loads(aliyun.get_allhost(region, PageNumber=page))
            instances = json_data['Instances']['Instance']
            page += 1
            if instances:
                instances = json_data['Instances']['Instance']
                for item in instances:
                    try:
                        ipaddr = item['VpcAttributes']['PrivateIpAddress']['IpAddress'][0]
                    except:
                        continue

                    try:
                        hostname = item['HostName']
                        host = Host.objects.get(Q(ipaddr=ipaddr) | Q(hostname=hostname))
                        host.hostname = hostname
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
            else:
                break

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
