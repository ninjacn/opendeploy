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

from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User

from deploy.models import Project, Task, Env, TaskHostRela
from opendeploy import settings
from .services import GitService, SvnService, DeployService, \
        ProjectService, EnvService, SettingService, MailService, MyLoggingService
from deploy.forms import ReleaseForm
from cmdb.services import QcloudService, AliyunService
from deploy.services import MyLoggingService

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
    d = DeployService(4)
    # d = DeployService(1, action=Task.ACTION_ROLLBACK)
    d.run()
    return HttpResponse('hello world')


@login_required
def release_log(request, id):
    rollback=request.GET.get('rollback')
    if rollback:
        filename = str(id) + '_rollback.log'
    else:
        filename = str(id) + '.log'
    file_path = os.path.join(settings.RELEASE_LOG_PATH[0], filename)
    try:
        with open(file_path, mode='r') as f:
            log_body = f.readlines()
    except:
        return HttpResponseNotFound("日志不存在")
    return HttpResponse(log_body, content_type='text/plain; charset=utf-8')

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
            task.creater = request.user
            task.comment = cleaned_data['comment']
            task.save()
            messages.info(request, '任务提交成功，准备发布...')
            return redirect('deploy:progress', task.id)
        else:
            messages.error(request, '任务申请校验失败, 请重新提交!')
    else:
        return redirect('deploy:homepage')

@login_required
def rollback(request, id):
    return redirect(reverse('deploy:progress', args=[id]) + '?rollback=1')

@login_required
def history(request):
    tasks = Task.objects.all().order_by('-id')

    param_status = request.GET.get('status')
    if param_status:
        tasks = tasks.filter(status=param_status)

    try:
        param_project = int(request.GET.get('project'))
        if param_project:
            tasks = tasks.filter(project=Project.objects.get(id=param_project))
    except:
        param_project = 0

    try:
        param_env = int(request.GET.get('env'))
        if param_env:
            tasks = tasks.filter(env=Env.objects.get(id=param_env))
    except:
        param_env = 0

    try:
        param_creater = int(request.GET.get('creater'))
        if param_creater:
            tasks = tasks.filter(creater=User.objects.get(id=param_creater))
    except:
        param_creater = 0

    paginator = Paginator(tasks, settings.PAGE_SIZE)
    page = request.GET.get('page')
    if not page:
        page = 1
    try:
        tasks_new = paginator.page(page)
    except PageNotAnInteger:
        tasks_new = paginator.page(1)
    except EmptyPage:
        tasks_new = paginator.page(paginator.num_pages)

    def rebuild_tasks(task):
        task.pretreatment = False
        task.long_comment = task.comment
        if len(task.comment) > 8:
            task.comment = task.comment[:8] + '...'
            task.pretreatment = True
        return task
    tasks = map(rebuild_tasks, tasks_new)

    get_copy = request.GET.copy()
    parameters = get_copy.pop('page', True) and get_copy.urlencode()
    return TemplateResponse(request, 'deploy/history.html', {
        'projects': Project.objects.filter(status=Project.STATUS_ENABLED),
        'creaters': User.objects.filter(is_active=1),
        'envs': Env.objects.all(),
        'status_choices': Task.STATUS_CHOICES,
        'tasks': tasks,
        'tasks_p': tasks_new, #分页数据，经过map之后tasks转换了list
        'param_status': param_status,
        'param_project': param_project,
        'param_env': param_env,
        'param_creater': param_creater,
        'parameters': parameters,
    })

@login_required
def detail(request, id):
    try:
        task = Task.objects.get(id=id)
    except:
        # return HttpResponseNotFound('<h1>Page not found</h1>')
        return redirect('deploy:tasks')
    taskHostRela = TaskHostRela.objects.filter(task=task)

    release_log_file_path = os.path.join(settings.RELEASE_LOG_PATH[0], str(id) + '.log')
    rollback_log_file_path = os.path.join(settings.RELEASE_LOG_PATH[0], str(id) + '_rollback.log')
    release_log = []
    try:
        with open(release_log_file_path, mode='r') as f:
            release_log = f.readlines()
    except:
        pass

    rollback_log = []
    try:
        with open(rollback_log_file_path, mode='r') as f:
            rollback_log = f.readlines()
    except:
        pass

    can_rollback=False
    if (task.status in [Task.STATUS_RELEASE_FINISH, Task.STATUS_RELEASE_FINISH_ERR]) and (task.status_rollback==Task.STATUS_ROLLBACK_WAIT):
        can_rollback=True
    return TemplateResponse(request, 'deploy/detail.html', {
        'task': task,
        'taskHostRela': taskHostRela,
        'release_log': ''.join(release_log),
        'rollback_log': ''.join(rollback_log),
        'can_rollback': can_rollback,
    })


@login_required
def progress(request, id):
    rollback = request.GET.get('rollback')
    try:
        task = Task.objects.get(id=id)
    except:
        return HttpResponseNotFound('<h1>Page not found</h1>')
    return TemplateResponse(request, 'deploy/progress.html', {
        'task': task,
        'rollback': rollback,
    })
