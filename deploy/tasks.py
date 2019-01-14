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


@app.task
def send_mail(tid, rollback=False):
    mailService = MailService()
    mailService.send_mail(tid, rollback)

@app.task
def send_notify(tid, rollback=False):
    try:
        task = Task.objects.get(id=tid)
        if task.project.enable_mail_notify:
            send_mail(tid, rollback)
    except:
        pass

    try:
        if task.project.dingding_robot_webhook:
            dingdingService = DingdingService()    
            dingdingService.send_chat_robot(task.project.dingding_robot_webhook, tid, rollback)
    except:
        pass
