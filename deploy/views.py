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

from django.shortcuts import render
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib.auth.decorators import login_required

from deploy.models import Project
from opendeploy import settings
from .services import GitService, SvnService, DeployService, \
        ProjectService, EnvService, SettingService, MailService

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
