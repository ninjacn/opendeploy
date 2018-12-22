# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import os
import logging
import json

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from deploy.models import Project, Task, Env
from opendeploy import settings
from .services import GitService, SvnService, DeployService, \
        ProjectService, EnvService, SettingService, MailService
from deploy.forms import ReleaseForm
from cmdb.services import QcloudService, AliyunService

# Create your views here.
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(name)s %(levelname)s %(message)s',
)
logger = logging.getLogger('app')

@login_required
def index(request):
    envService = EnvService()
    envs = envService.get_all()
    projectService = ProjectService()
    projects = projectService.get_valid_all()
    return TemplateResponse(request, 'deploy/index.html', {
        'envs': envs,
        'projects': projects,
    })

def test(request):
    # DEPLOY_MODE_ALL
    # DEPLOY_MODE_INCREMENT
    d = DeployService(6, 4, mode=Project.DEPLOY_MODE_ALL)
    d.run()
    return HttpResponse('hello world')

@login_required
def release(request):
    if request.method == 'POST':
        f = ReleaseForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            task = Task()
            try:
                project = Project.objects.get(id=cleaned_data['project'])
            except:
                messages.error(request, '项目不存在!')
                return redirect('deploy:homepage')

            try:
                env = Env.objects.get(id=cleaned_data['env'])
            except:
                messages.error(request, '环境不存在!')
                return redirect('deploy:homepage')

            task.project = project
            task.env = env
            task.comment = cleaned_data['comment']
            task.save()
            messages.info(request, '任务提交成功，准备发布...')
            return redirect('deploy:tasks')
        else:
            messages.error(request, '任务申请校验失败, 请重新提交!')
    else:
        return redirect('deploy:homepage')

@login_required
def rollback(request, id):
    pass

@login_required
def tasks(request):
    tasks = Task.objects.all().order_by('-id')
    paginator = Paginator(tasks, 2)
    page = request.GET.get('page')
    if not page:
        page = 1
    try:
        tasks = paginator.page(page)
    except PageNotAnInteger:
        tasks = paginator.page(1)
    except EmptyPage:
        tasks = paginator.page(paginator.num_pages)
    return TemplateResponse(request, 'deploy/tasks.html', {
        # 'envs': envs,
        'tasks': tasks,
    })

@login_required
def detail(request, id):
    pass
