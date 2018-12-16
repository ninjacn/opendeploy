# -*- coding: utf-8 -*-
from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from admin.forms import AddEnvForm, AddProjectForm, AddCredentialForPasswordForm
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
                project.dest_rootpath = cleaned_data['dest_rootpath']
                project.comment = cleaned_data['comment']
                project.deploy_mode = cleaned_data['deploy_mode']
                project.status = cleaned_data['status']
                project.save()

                # 增加环境关联值
                envs = request.POST.getlist('env')
                if envs:
                    for env in envs:
                        projectEnvConfig = ProjectEnvConfig()
                        projectEnvConfig.pid = project.id
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
    if request.method== 'POST':
        f = AddProjectForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                project.name = cleaned_data['name']
                project.vcs_type = cleaned_data['vcs_type']
                project.repository_url = cleaned_data['repository_url']
                project.credentials = Credentials.objects.get(id=cleaned_data['credential'])
                project.dest_rootpath = cleaned_data['dest_rootpath']
                project.comment = cleaned_data['comment']
                project.deploy_mode = cleaned_data['deploy_mode']
                project.status = cleaned_data['status']
                project.save()

                # 增加环境关联值
                envs = request.POST.getlist('projectEnvConfig')
                if envs:
                    for v in envs:
                        config = ProjectEnvConfig.objects.get(pk=v)
                        config.branch = request.POST.get('branch_' + v)
                        config.host_group = HostGroup.objects.get(pk=request.POST.get('host_group_' + v))
                        config.save()
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
                    credential.passphrase = cleaned_data['passphrase']
                credential.save()
            finally:
                return redirect('/admin/deploy/credential')
    else:
        f = AddCredentialForPasswordForm()
    return render(request, 'admin/deploy/add_credential.html', {
        "form": f,
        "type_choices": Credentials.TYPE_CHOICES,
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
                pass
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
    })

