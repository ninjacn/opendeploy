# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2019-01-06
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import json
import logging
from pprint import pprint, pformat

from django.contrib.auth.models import User
from django.shortcuts import render
from django.urls import reverse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse, HttpResponseServerError
from django.core.exceptions import ObjectDoesNotExist

from api.models import Token
from deploy.models import Project, Env, ProjectEnvConfig
from deploy.services import ProjectService
from common.services import WebhookRequestBodyOfGitlabService, WebhookRequestBodyOfGithubService
from deploy.tasks import release as task_release 

logger = logging.getLogger('webhook')

def check_api_token(func):
    def func_wrapper(request, *args, **kwargs):
        res = {
            'error_code': 10000,
            'msg': '非法请求, 请求方法必须为POST，或token不正确',
        }
        try:
            Token.objects.get(token=request.GET.get('token'))
            if request.method == 'POST':
                return func(request, *args, **kwargs)
        except:
            pass
        return JsonResponse(res, safe=False, status=500)
    return func_wrapper

@csrf_exempt
@check_api_token
def webhook_gitlab(request, pid, env_id):
    logger.info('request path:' + request.get_full_path())
    logger.info('request header:')
    logger.info(pformat(request.META))
    logger.info('request body:')
    try:
        gitlabService = WebhookRequestBodyOfGitlabService(request)
        request_body = gitlabService.get_body()
        logger.info(pformat(request_body))
    except RuntimeError as e:
        logger.error(str(e))
        logger.error(pformat(request.body))
        return HttpResponse(str(e), status=500)
    except:
        logger.error('未知问题')
        return HttpResponse('未知问题', status=500)
    try:
        project = Project.objects.get(id=pid)
    except:
        return HttpResponseNotFound('项目没找到')
    if project.repository_url not in githubService.get_urls():
        return HttpResponseNotFound('项目Url不匹配')
    try:
        env = Env.objects.get(id=env_id)
    except:
        return HttpResponseNotFound('环境没找到')
    try:
        projectEnvConfig = ProjectEnvConfig.objects.get(project=project, env=env)
    except:
        return HttpResponseNotFound('项目环境配置未匹配')
    events = ['push', 'merge_request']
    if request_body['object_kind'] not in events:
        return HttpResponseNotFound('只支持push及merge_request事件')
    logger.info('branch_name:' + gitlabService.get_branch_name())
    if projectEnvConfig.branch != gitlabService.get_branch_name():
        logger.error('项目环境配置中分支名不匹配')
        return HttpResponseNotFound('项目环境配置中分支名不匹配')
    comment = gitlabService.get_comment()
    try:
        projectService = ProjectService(pid)
        creater = User.objects.get(username='git_robot')
        task = projectService.create_task(env_id, creater, comment)
        task_release.delay(task.id)
        return HttpResponse('创建成功, url:' + reverse('deploy:detail', args=[task.id]))
    except (RuntimeError, ObjectDoesNotExist) as e:
        return HttpResponse(str(e), status=500)
    except:
        return HttpResponse('创建失败，未知异常', status=500)

@csrf_exempt
@check_api_token
def webhook_github(request, pid, env_id):
    logger.info('request path:' + request.get_full_path())
    logger.info('request header:')
    logger.info(pformat(request.META))
    logger.info('request body:')
    try:
        githubService = WebhookRequestBodyOfGithubService(request)
        request_body = githubService.get_body()
        logger.info(pformat(request_body))
    except RuntimeError as e:
        logger.error(str(e))
        logger.error(pformat(request.body))
        return HttpResponse(str(e), status=500)
    except:
        logger.error('未知问题')
        return HttpResponse('未知问题', status=500)
    try:
        project = Project.objects.get(id=pid)
    except:
        return HttpResponseNotFound('项目没找到')
    if project.repository_url not in githubService.get_urls():
        return HttpResponseNotFound('项目Url不匹配')
    try:
        env = Env.objects.get(id=env_id)
    except:
        return HttpResponseNotFound('环境没找到')
    try:
        projectEnvConfig = ProjectEnvConfig.objects.get(project=project, env=env)
    except:
        return HttpResponseNotFound('项目环境配置未匹配')
    logger.info('branch_name:' + githubService.get_branch_name())
    if projectEnvConfig.branch != githubService.get_branch_name():
        logger.error('项目环境配置中分支名不匹配')
        return HttpResponseNotFound('项目环境配置中分支名不匹配')
    comment = githubService.get_comment()
    try:
        projectService = ProjectService(pid)
        creater = User.objects.get(username='git_robot')
        task = projectService.create_task(env_id, creater, comment)
        task_release.delay(task.id)
        return HttpResponse('创建成功, url:' + reverse('deploy:detail', args=[task.id]))
    except (RuntimeError, ObjectDoesNotExist) as e:
        return HttpResponse(str(e), status=500)
    except:
        return HttpResponse('创建失败，未知异常', status=500)

@csrf_exempt
@login_required
@transaction.atomic
def get_hosts(request, pid, env_id):
    try:
        projectService = ProjectService(pid)
        all_host = projectService.get_all_host_with_extra(env_id)
    except:
        all_host = []
    return JsonResponse(all_host, safe=False, status=200)
