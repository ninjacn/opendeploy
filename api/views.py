# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2019-01-06
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound


@csrf_exempt
@login_required
def webhook_gitlab(pid, env_id):
    print(pid)
    print(env_id)
    return HttpResponse('webhook_gitlab')

@csrf_exempt
@login_required
def webhook_github(pid, env_id):
    print(pid)
    print(env_id)
    return HttpResponse('webhook_github')
