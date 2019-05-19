# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import os
import io
import stat

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from opendeploy import settings
from admin.forms import AddEnvForm, ProjectForm, AddCredentialForPasswordForm, \
        AddCredentialForPrivateForm
from deploy.models import Env, Project, ProjectEnvConfig,  \
        Credentials
from cmdb.models import HostGroup
from common.services import CommandService
from setting.services import SettingService

# Create your views here.

@user_passes_test(lambda u: u.is_superuser)
def index(request):
    return render(request, 'base_admin.html')

@user_passes_test(lambda u: u.is_superuser)
def project(request):
    q = request.GET.get('q')
    if q:
        projects = Project.objects.filter(Q(name__contains=q) | Q(repository_url__contains=q)).order_by('-status', '-updated_at')
    else:
        projects = Project.objects.all().order_by('-status', '-updated_at')
    paginator = Paginator(projects, settings.PAGE_SIZE)
    page = request.GET.get('page')
    if not page:
        page = 1
    try:
        projects = paginator.page(page)
    except PageNotAnInteger:
        projects = paginator.page(1)
    except EmptyPage:
        projects = paginator.page(paginator.num_pages)

    get_copy = request.GET.copy()
    parameters = get_copy.pop('page', True) and get_copy.urlencode()
    return render(request, 'admin/deploy/project.html', {
        "projects": projects,
        'parameters': parameters,
        'q': q,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def project_add(request):
    if request.method== 'POST':
        f = ProjectForm(request.POST)
        if f.is_valid():
            try:
                cleaned_data = f.cleaned_data
                project = Project()
                project.name = cleaned_data['name']
                project.vcs_type = cleaned_data['vcs_type']
                project.repository_url = cleaned_data['repository_url']
                project.credentials = cleaned_data['credentials']
                project.dest_path = cleaned_data['dest_path']
                project.comment = cleaned_data['comment']
                project.deploy_mode = cleaned_data['deploy_mode']
                project.dingding_robot_webhook = cleaned_data['dingding_robot_webhook']
                project.status = cleaned_data['status']
                project.exclude_file = cleaned_data['exclude_file']
                project.rsync_enable_delete = cleaned_data['rsync_enable_delete']
                project.enable_mail_notify = cleaned_data['enable_mail_notify']
                project.save()
                exclude_file_path = os.path.join(settings.BASE_DIR, 'storage/exclude_file/' + str(project.id))
                if len(project.exclude_file) > 0:
                    with open(exclude_file_path, 'w') as f:
                        f.write(project.exclude_file)

                # 增加环境关联值
                envs = request.POST.getlist('env')
                if envs:
                    for env in envs:
                        projectEnvConfig = ProjectEnvConfig()
                        projectEnvConfig.project = project
                        try:
                            projectEnvConfig.env = Env.objects.get(pk=env)
                        except:
                            pass
                        projectEnvConfig.branch = request.POST.get('branch_' + env)
                        projectEnvConfig.before_hook = request.POST.get('before_hook_' + env)
                        projectEnvConfig.after_hook = request.POST.get('after_hook_' + env)
                        if request.POST.get('host_group_' + env):
                            try:
                                projectEnvConfig.host_group = HostGroup.objects.get(pk=request.POST.get('host_group_' + env))
                            except:
                                pass
                        projectEnvConfig.save()

                        before_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/before_hook_' + str(projectEnvConfig.id))
                        if len(projectEnvConfig.before_hook) > 0:
                            with open(before_hook_path, 'w') as f:
                                f.write(projectEnvConfig.before_hook)

                        after_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/after_hook_' + str(projectEnvConfig.id))
                        if len(projectEnvConfig.after_hook) > 0:
                            with open(after_hook_path, 'w') as f:
                                f.write(projectEnvConfig.after_hook)

                        if os.path.exists(before_hook_path):
                            os.chmod(before_hook_path, stat.S_IRWXU)
                            command = 'dos2unix ' + before_hook_path
                            CommandService(command)

                        if os.path.exists(after_hook_path):
                            os.chmod(after_hook_path, stat.S_IRWXU)
                            command = 'dos2unix ' + after_hook_path
                            CommandService(command)
                    messages.info(request, '添加成功')
            except:
                messages.error(request, '添加失败')
            finally:
                return redirect('admin:deploy.project')
        else:
            messages.error(request, '表单校验失败')
    else:
        f = ProjectForm()
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
def project_edit(request, id):
    project = Project.objects.get(pk=id)
    projectEnvConfig = ProjectEnvConfig.objects.filter(project=project)
    # 该项目环境id列表
    env_list_by_project = []
    for v in projectEnvConfig:
        env_list_by_project.append(v.env.id)

    if request.method== 'POST':
        f = ProjectForm(request.POST, instance=project)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                f.save()
                exclude_file_path = os.path.join(settings.BASE_DIR, 'storage/exclude_file/' + str(id))
                if len(cleaned_data['exclude_file']) > 0:
                    with open(exclude_file_path, 'w') as f:
                        f.write(cleaned_data['exclude_file'].encode())
                else:
                    if os.path.exists(exclude_file_path):
                        os.unlink(exclude_file_path)
                # 增加环境关联值
                envs = request.POST.getlist('projectEnvConfig')
                if envs:
                    for v in envs:
                        # 存在更新
                        try:
                            config = ProjectEnvConfig.objects.get(pk=v)
                            if request.POST.get('branch_' + v):
                                config.branch = request.POST.get('branch_' + v)
                            else:
                                config.branch = 'master'
                            config.before_hook = request.POST.get('before_hook_' + v, '')
                            config.after_hook = request.POST.get('after_hook_' + v, '')
                            if request.POST.get('host_group_' + v):
                                config.host_group = HostGroup.objects.get(pk=request.POST.get('host_group_' + v))
                            config.save()

                            before_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/before_hook_' + str(config.id))
                            if len(config.before_hook)>0:
                                with open(before_hook_path, 'w') as f:
                                    f.write(config.before_hook)
                            else:
                                if os.path.exists(before_hook_path):
                                    os.unlink(before_hook_path)

                            after_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/after_hook_' + str(config.id))
                            if len(config.after_hook)>0:
                                with open(after_hook_path, 'w') as f:
                                    f.write(config.after_hook)
                            else:
                                if os.path.exists(after_hook_path):
                                    os.unlink(after_hook_path)

                            if os.path.exists(before_hook_path):
                                os.chmod(before_hook_path, stat.S_IRWXU)
                                command = 'dos2unix ' + before_hook_path
                                CommandService(command)

                            if os.path.exists(after_hook_path):
                                os.chmod(after_hook_path, stat.S_IRWXU)
                                command = 'dos2unix ' + after_hook_path
                                CommandService(command)
                        # 不存在插入
                        except:
                            projectEnvConfig = ProjectEnvConfig()
                            projectEnvConfig.project = project
                            projectEnvConfig.env = Env.objects.get(pk=v)
                            if request.POST.get('branch_' + v):
                                projectEnvConfig.branch = request.POST.get('branch_' + v)
                            else:
                                projectEnvConfig.branch = 'master'
                            if request.POST.get('host_group_' + v):
                                projectEnvConfig.host_group = HostGroup.objects.get(pk=request.POST.get('host_group_' + v))
                            projectEnvConfig.before_hook = request.POST.get('before_hook_' + v, '')
                            projectEnvConfig.after_hook = request.POST.get('after_hook_' + v, '')
                            projectEnvConfig.save()

                            before_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/before_hook_' + str(projectEnvConfig.id))
                            with open(before_hook_path, 'w') as f:
                                f.write(projectEnvConfig.before_hook)

                            after_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/after_hook_' + str(projectEnvConfig.id))
                            with open(after_hook_path, 'w') as f:
                                f.write(projectEnvConfig.after_hook)

                            if os.path.exists(before_hook_path):
                                os.chmod(before_hook_path, stat.S_IRWXU)
                                command = 'dos2unix ' + before_hook_path
                                CommandService(command)

                            if os.path.exists(after_hook_path):
                                os.chmod(after_hook_path, stat.S_IRWXU)
                                command = 'dos2unix ' + after_hook_path
                                CommandService(command)
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('admin:deploy.project')
    else:
        f = ProjectForm()
    settingService = SettingService()
    general_info = settingService.get_general_info()
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
        "general_info": general_info,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def project_del(request, id):
    try:
        project = Project.objects.get(id=id)
        project.delete()
        messages.info(request, '删除成功')
    except:
        messages.error(request, '删除失败')
    return redirect('admin:deploy.project')

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
@transaction.atomic
def env_edit(request, id):
    env = Env.objects.get(pk=id)
    if request.method== 'POST':
        f = AddEnvForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                env.name = cleaned_data['name']
                env.comment = cleaned_data['comment']
                env.save()
                messages.info(request, '修改成功')
            except:
                messages.error(request, '修改失败')
            finally:
                return redirect('admin:deploy.env')
    else:
        f = AddEnvForm()
    return render(request, 'admin/deploy/edit_env.html', {
        "form": f,
        "env": env,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def env_del(request, id):
    try:
        env = Env.objects.get(id=id)
        env.delete()
        messages.info(request, '删除成功')
    except:
        messages.error(request, '删除失败')
    return redirect('admin:deploy.env')


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
                    key_path = os.path.join(settings.BASE_DIR, 'storage/privary_key/' + str(credential.id))
                    if len(credential.private_key) > 0:
                        with open(key_path, 'w') as f:
                            f.write(credential.private_key)
                        os.chmod(key_path, stat.S_IRWXU)
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
def credential_edit(request, id):
    credential = Credentials.objects.get(pk=id)
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
                    if len(credential.private_key) > 0:
                        with open(key_path, 'w') as f:
                            f.write(credential.private_key.rstrip() + '\n')
                        command = 'dos2unix ' + key_path
                        CommandService(command)
                        os.chmod(key_path, stat.S_IRWXU)
                    else:
                        if os.path.exists(key_path):
                            os.unlink(key_path)
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

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def credential_del(request, id):
    try:
        credentials = Credentials.objects.get(id=id)
        credentials.delete()
        messages.info(request, '删除成功')
    except:
        messages.error(request, '删除失败')
    return redirect('admin:deploy.credential')

