# -*- coding: utf-8 -*-
from django.shortcuts import (render, redirect)
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.db import transaction
from admin.forms import *
from deploy.models import (Env,)
from cmdb.models import (Host, HostGroup)

# Create your views here.

def host(request):
    hosts = Host.objects.all()
    return TemplateResponse(request, 'admin/cmdb/host.html', {
        "hosts": hosts,
    })

@transaction.atomic
def add_host(request):
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
    return TemplateResponse(request, 'admin/cmdb/add_host.html', {
        "form": f,
        "status_choices": Host.STATUS_CHOICES,
    })

@transaction.atomic
def edit_host(request, id):
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
    return TemplateResponse(request, 'admin/cmdb/edit_host.html', {
        "form": f,
        "host": host,
        "status_choices": Host.STATUS_CHOICES,
    })

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
    print(data)
    return TemplateResponse(request, 'admin/cmdb/hostgroup.html', {
        "data": data,
        "hostGroup": hostGroup,
    })

@transaction.atomic
def add_hostgroup(request):
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
    return TemplateResponse(request, 'admin/cmdb/add_hostgroup.html', {
        "form": f,
        "hosts": Host.objects.filter(status=Host.STATUS_ENABLED),
        "status_choices": HostGroup.STATUS_CHOICES,
    })

@transaction.atomic
def edit_hostgroup(request, gid):
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
    return TemplateResponse(request, 'admin/cmdb/edit_hostgroup.html', {
        "form": f,
        "hostgroup": hostgroup,
        "hosts": Host.objects.filter(status=Host.STATUS_ENABLED),
        "status_choices": HostGroup.STATUS_CHOICES,
    })
