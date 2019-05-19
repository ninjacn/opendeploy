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
import time
import base64
import subprocess

from django.shortcuts import render, redirect, reverse
from django.contrib import messages
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.db import transaction
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.core.cache import cache

from opendeploy.celery import app
from deploy.models import Project, Task, Env, TaskHostRela, ProjectEnvConfig
from opendeploy import settings
from deploy.services import GitService, SvnService, DeployService, \
        ProjectService, EnvService, SettingService, MyLoggingService
from common.services import MailService, CommandService
from deploy.forms import ReleaseForm
from cmdb.services import QcloudService, AliyunService
from deploy.tasks import release as task_release 

# Create your views here.
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(name)s %(levelname)s %(message)s',
)
logger = logging.getLogger('app')

@login_required
@transaction.atomic
def index(request):
    envService = EnvService()
    envs = envService.get_all()
    projectService = ProjectService()
    projects = projectService.get_valid_all()
    f = ReleaseForm()
    return TemplateResponse(request, 'deploy/index.html', {
        'form': f,
        'envs': envs,
        'projects': projects,
    })

def test(request):
    hosts_list = ['192.168.1.111', '192.168.1.112']
    queue = task_release.delay(141, rollback=False, hosts_list=hosts_list)
    return HttpResponse('hello world')


@login_required
@transaction.atomic
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
@transaction.atomic
def release(request):
    if request.method == 'POST':
        f = ReleaseForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            pid = cleaned_data['project']
            env_id = cleaned_data['env']
            comment = cleaned_data['comment']
            scope = cleaned_data['scope']
            files_list = cleaned_data['files_list']
            try:
                projectService = ProjectService(pid)
                task = projectService.create_task(env_id, request.user, comment, scope, files_list)

                queue = task_release.delay(task.id)
                task.celery_task_id = queue.id
                task.save()
                messages.info(request, '任务提交成功，准备发布...')
                return redirect('deploy:progress', task.id)
            except RuntimeError as e:
                messages.error(request, str(e))
                return redirect('deploy:homepage')
        else:
            messages.error(request, '任务申请校验失败, 请重新提交!')
            print(f.errors)
            envService = EnvService()
            envs = envService.get_all()
            projectService = ProjectService()
            projects = projectService.get_valid_all()
            return TemplateResponse(request, 'deploy/index.html', {
                'form': f,
                'envs': envs,
                'projects': projects,
            })
    else:
        return redirect('deploy:homepage')

@login_required
@transaction.atomic
def rollback(request, id):
    task_release.delay(id, rollback=True)
    return redirect(reverse('deploy:progress', args=[id]) + '?rollback=1')

@login_required
@transaction.atomic
def history(request):
    tasks = Task.objects.all().order_by('-id')

    try:
        param_status = int(request.GET.get('status'))
        tasks = tasks.filter(status=param_status)
    except:
        param_status = None


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
@transaction.atomic
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
@transaction.atomic
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

@login_required
@csrf_exempt
def release_status(request, id):
    data = {
        'percent_value': 0,
        'log_body': '',
    }
    rollback=request.GET.get('rollback')
    if rollback:
        filename = str(id) + '_rollback.log'
        percent_key = 'opendeploy:percent:rollback:' + str(id)
    else:
        filename = str(id) + '.log'
        percent_key = 'opendeploy:percent:' + str(id)
    file_path = os.path.join(settings.RELEASE_LOG_PATH[0], filename)
    try:
        with open(file_path, mode='r') as f:
            data['log_body'] = f.readlines()
    except:
        pass
    percent_value = cache.get(percent_key)
    if percent_value:
        data['percent_value'] = percent_value
    else:
        data['percent_value'] = 0
    return JsonResponse(data)

@login_required
@transaction.atomic
def diff(request, id):
    diff = ''
    diff_errmsg = []
    diff_okmsg = []
    try:
        task = Task.objects.get(id=id)
        pre_task = Task.objects.filter(project=task.project, env=task.env, id__lt=task.id) \
                .exclude(version__exact='') \
                .order_by('-id').first()
        projectEnvConfig = ProjectEnvConfig.objects.get(project=task.project, env=task.env)
    except:
        return HttpResponseNotFound('<h1>Page not found</h1>')

    if task and pre_task and task.version and pre_task.version:
        if task.project.vcs_type == 'svn':
            if task.scope == Task.SCOPE_BY_FILE:
                for item in task.files_list.splitlines():
                    command = 'cd ' + settings.WORKSPACE_PATH + '/' + str(task.project.id) + \
                            ' && svn --non-interactive --username=' + task.project.credentials.username + \
                            ' --password=' + task.project.credentials.password + ' diff --git  -r ' + pre_task.version + ':' + task.version + \
                            ' ' + item
                    completed = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if completed.returncode > 0:
                        diff_errmsg.append(completed.stderr)
                    else:
                        if len(completed.stdout) <= 0:
                            diff_okmsg.append(item + ' 文件内容比对相同.')
                        diff += completed.stdout.decode('utf-8')
            else:
                command = 'cd ' + settings.WORKSPACE_PATH + '/' + str(task.project.id) + \
                        ' && svn --non-interactive --username=' + task.project.credentials.username + \
                        ' --password=' + task.project.credentials.password + ' diff --git  -r ' + pre_task.version + ':' + task.version
                completed = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if completed.returncode > 0:
                    diff_errmsg.append(completed.stderr)
                else:
                    diff += completed.stdout.decode('utf-8')
        else:
            if task.scope == Task.SCOPE_BY_FILE:
                for item in task.files_list.splitlines():
                    command = 'cd ' + settings.WORKSPACE_PATH + '/' + str(task.project.id) + '_' + \
                            projectEnvConfig.branch + ' && git diff '  + pre_task.version + ':' + item + ' ' + \
                            task.version + ':' + item
                    completed = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    if completed.returncode > 0:
                        diff_errmsg.append(completed.stderr)
                    else:
                        if len(completed.stdout) <= 0:
                            diff_okmsg.append(item + ' 文件内容比对相同.')
                        diff += completed.stdout.decode('utf-8')
            else:
                command = 'cd ' + settings.WORKSPACE_PATH + '/' + str(task.project.id) + '_' + \
                    projectEnvConfig.branch + ' && git diff '  + pre_task.version + ' ' + task.version
                completed = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if completed.returncode > 0:
                    diff_errmsg.append(completed.stderr)
                else:
                    diff += completed.stdout.decode('utf-8')
    else:
        return HttpResponseNotFound('<h1>版本信息未找到，无法diff</h1>')
    if len(diff_errmsg) <= 0 and len(diff) <= 0:
        diff_okmsg.append('所有文件内容比对相同.')
    return TemplateResponse(request, 'deploy/diff.html', {
        'task': task,
        'diff_errmsg': diff_errmsg,
        'diff_okmsg': diff_okmsg,
        'diffString': base64.b64encode(diff.encode('utf-8')).decode('utf-8'),
    })
