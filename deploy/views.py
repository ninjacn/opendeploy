# -*- coding: utf-8 -*-
# Author: Pengming Yao<x@ninjacn.com>
# Date created: 2018-12-16

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
    # d = DeployService(9, 4)
    return HttpResponse('hello world')
