# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.conf.urls import url

from . import views

app_name='deploy'

urlpatterns = [
    url(r'^$', views.index, name='homepage'),
    url(r'^task/release$', views.release, name='release'),
    url(r'^task/rollback/(?P<id>\d+)$', views.rollback, name='rollback'),
    url(r'^task/progress/(?P<id>\d+)', views.progress, name='progress'),
    url(r'^task/history$', views.history, name='history'),
    url(r'^task/detail/(?P<id>\d+)$', views.detail, name='detail'),
    url(r'^task/diff/(?P<id>\d+)$', views.diff, name='diff'),
    url(r'^task/release-log/(?P<id>\d+)', views.release_log, name='release_log'),
    url(r'^task/get-release-status/(?P<id>\d+)', views.release_status, name='release_status'),
    url(r'^task/$', views.history),
]
