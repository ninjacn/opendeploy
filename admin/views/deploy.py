# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import os

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from opendeploy import settings

from admin.forms import AddEnvForm, AddProjectForm, AddCredentialForPasswordForm, \
        AddCredentialForPrivateForm
from deploy.models import Env, Project, ProjectEnvConfig,  \
        Credentials
from cmdb.models import HostGroup

# Create your views here.

@user_passes_test(lambda u: u.is_superuser)
def index(request):
    return render(request, 'base_admin.html')

@user_passes_test(lambda u: u.is_superuser)
def project(request):
    projects = Project.objects.all()
    return render(request, 'admin/deploy/project.html', {
        "projects": projects,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def project_add(request):
    if request.method== 'POST':
        f = AddProjectForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                project = Project()
                project.name = cleaned_data['name']
                project.vcs_type = cleaned_data['vcs_type']
                project.repository_url = cleaned_data['repository_url']
                project.credentials = Credentials.objects.get(id=cleaned_data['credential'])
                project.dest_path = cleaned_data['dest_path']
                project.comment = cleaned_data['comment']
                project.deploy_mode = cleaned_data['deploy_mode']
                project.status = cleaned_data['status']
                project.save()

                # 增加环境关联值
                envs = request.POST.getlist('env')
                if envs:
                    for env in envs:
                        projectEnvConfig = ProjectEnvConfig()
                        projectEnvConfig.project = project
                        projectEnvConfig.env = Env.objects.get(pk=env)
                        projectEnvConfig.branch = request.POST.get('branch_' + env)
                        projectEnvConfig.host_group = HostGroup.objects.get(pk=request.POST.get('host_group_' + env))
                        projectEnvConfig.save()
            finally:
                return redirect('/admin/deploy/project')
    else:
        f = AddProjectForm()
    return render(request, 'admin/deploy/add_project.html', {
        "form": f,
        "status_choices": Project.STATUS_CHOICES,
        "type_choices": Project.TYPE_CHOICES,
        "credentials": Credentials.objects.all(),
        "deploy_mode_choices": Project.DEPLOY_MODE_CHOICES,
        "envlist": Env.objects.all(),
        "host_group": HostGroup.objects.all(),
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def project_edit(request, gid):
    project = Project.objects.get(pk=gid)
    projectEnvConfig = ProjectEnvConfig.objects.filter(project=project)
    # 该项目环境id列表
    env_list_by_project = []
    for v in projectEnvConfig:
        env_list_by_project.append(v.env.id)

    if request.method== 'POST':
        f = AddProjectForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                project.name = cleaned_data['name']
                project.vcs_type = cleaned_data['vcs_type']
                project.repository_url = cleaned_data['repository_url']
                project.credentials = Credentials.objects.get(id=cleaned_data['credential'])
                project.dest_path = cleaned_data['dest_path']
                project.comment = cleaned_data['comment']
                project.deploy_mode = cleaned_data['deploy_mode']
                project.status = cleaned_data['status']
                project.save()

                # 增加环境关联值
                envs = request.POST.getlist('projectEnvConfig')
                if envs:
                    for v in envs:
                        # 存在更新
                        try:
                            config = ProjectEnvConfig.objects.get(pk=v)
                            config.branch = request.POST.get('branch_' + v)
                            try:
                                config.host_group = HostGroup.objects.get(pk=request.POST.get('host_group_' + v))
                            except:
                                config.host_group = None
                            config.save()
                        # 不存在插入
                        except:
                            projectEnvConfig = ProjectEnvConfig()
                            projectEnvConfig.project = project
                            projectEnvConfig.env = Env.objects.get(pk=v)
                            if request.POST.get('branch_' + v):
                                projectEnvConfig.branch = request.POST.get('branch_' + v)
                            else:
                                projectEnvConfig.branch = 'master'
                            projectEnvConfig.host_group = HostGroup.objects.get(pk=request.POST.get('host_group_' + v))
                            projectEnvConfig.save()
            finally:
                return redirect('/admin/deploy/project')
    else:
        f = AddProjectForm()
    return render(request, 'admin/deploy/edit_project.html', {
        "form": f,
        "project": project,
        "projectEnvConfig": projectEnvConfig,
        "status_choices": Project.STATUS_CHOICES,
        "type_choices": Project.TYPE_CHOICES,
        "deploy_mode_choices": Project.DEPLOY_MODE_CHOICES,
        "envlist": Env.objects.all(),
        "host_group": HostGroup.objects.all(),
        "credentials": Credentials.objects.all(),
        "env_list_by_project": env_list_by_project,
    })

@user_passes_test(lambda u: u.is_superuser)
def env(request):
    envs = Env.objects.all()
    return render(request, 'admin/deploy/env.html', {
        "envs": envs
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def env_add(request):
    if request.method== 'POST':
        f = AddEnvForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                env = Env()
                env.name = cleaned_data['name']
                env.comment = cleaned_data['comment']
                env.save()
            finally:
                return redirect('/admin/deploy/env')
    else:
        f = AddEnvForm()
    return render(request, 'admin/deploy/env_add.html', {
        "form": f,
        })

@user_passes_test(lambda u: u.is_superuser)
def credential(request):
    credentials = Credentials.objects.all()
    return render(request, 'admin/deploy/credential.html', {
        "credentials": credentials,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def credential_add(request):
    if request.method== 'POST':
        auth_type = int(request.POST.get('type'))
        if auth_type == Credentials.TYPE_USER_PWD:
            f = AddCredentialForPasswordForm(request.POST)
        else:
            f = AddCredentialForPrivateForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                credential = Credentials()
                credential.type = auth_type
                credential.username = cleaned_data['username']
                credential.comment = cleaned_data['comment']
                if auth_type == Credentials.TYPE_USER_PWD:
                    credential.password = cleaned_data['password']
                else:
                    credential.private_key = cleaned_data['private_key']
                credential.save()

                if auth_type != Credentials.TYPE_USER_PWD:
                    key_path = os.path.join(settings.BASE_DIR, 'storage/privary_key/' + credential.id)
                    f = open(key_path, 'w+')
                    f.write(credential.private_key)
                    f.close()
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('/admin/deploy/credential')
    else:
        f = AddCredentialForPasswordForm()
    return render(request, 'admin/deploy/add_credential.html', {
        "form": f,
        "type_choices": Credentials.TYPE_CHOICES,
        "type_user_pwd": Credentials.TYPE_USER_PWD,
        })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def credential_edit(request, gid):
    credential = Credentials.objects.get(pk=gid)
    auth_type = credential.type
    if request.method== 'POST':
        if auth_type == Credentials.TYPE_USER_PWD:
            f = AddCredentialForPasswordForm(request.POST)
        else:
            f = AddCredentialForPrivateForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                credential.type = auth_type
                credential.username = cleaned_data['username']
                credential.comment = cleaned_data['comment']
                if auth_type == Credentials.TYPE_USER_PWD:
                    credential.password = cleaned_data['password']
                else:
                    credential.private_key = cleaned_data['private_key']
                credential.save()
                if auth_type != Credentials.TYPE_USER_PWD:
                    key_path = os.path.join(settings.BASE_DIR, 'storage/privary_key/' + str(credential.id))
                    f = open(key_path, 'w+')
                    f.write(credential.private_key)
                    f.close()
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('/admin/deploy/credential')
    else:
        if auth_type == Credentials.TYPE_USER_PWD:
            f = AddCredentialForPasswordForm()
        else:
            f = AddCredentialForPrivateForm()
    return render(request, 'admin/deploy/edit_credential.html', {
        "form": f,
        "credential": credential,
        "type_choices": Credentials.TYPE_CHOICES,
        "auth_type": auth_type,
        "type_user_pwd": Credentials.TYPE_USER_PWD,
    })

