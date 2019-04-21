# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from __future__ import absolute_import, unicode_literals
from opendeploy.celery import app
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from common.services import MailService, DingdingService
from deploy.models import Task
from deploy.services import DeployService


@app.task
def release(tid, rollback=False, hosts_list=[]):
    if rollback:
        deployService = DeployService(tid, action=Task.ACTION_ROLLBACK, hosts_list=hosts_list)
    else:
        deployService = DeployService(tid, hosts_list=hosts_list)
    deployService.run()

@app.task
def send_mail(tid, rollback=False):
    mailService = MailService()
    mailService.send_mail(tid, rollback)
