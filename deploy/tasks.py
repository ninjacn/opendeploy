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
from .services import MailService

@app.task
def add(x, y):
    return x + y

@app.task
def send_mail():
    mailService = MailService()
    mailService.send_mail()
