# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-24
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.conf.urls import url

from . import views

app_name='api'

urlpatterns = [
    url(r'^webhook/gitlab/(?P<pid>\d+)-(?P<env_id>\d+)', views.webhook_gitlab, name='webhook_gitlab'),
    url(r'^webhook/github/(?P<pid>\d+)-(?P<env_id>\d+)', views.webhook_github, name='webhook_github'),
    url(r'^deploy/get-hosts/(?P<pid>\d+)-(?P<env_id>\d+)', views.get_hosts, name='get_hosts'),
]
