import os
import logging

from django.shortcuts import render
from django.http import HttpResponse
from django.template.response import TemplateResponse
from deploy.models import Project
from opendeploy import settings
from .services import GitService, SvnService, DeployService, ProjectService, EnvService

# Create your views here.
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(name)s %(levelname)s %(message)s',
)
logger = logging.getLogger('app')


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
    logger.info('info')
    logger.error('error')
    logger.debug('debug')
    return HttpResponse('hello world')
