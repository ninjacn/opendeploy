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
    url(r'^release$', views.release, name='release'),
    url(r'^rollback/(?P<id>\d+)$', views.rollback, name='rollback'),
    url(r'^tasks/$', views.tasks, name='tasks'),
    url(r'^detail/(?P<id>\d+)$', views.detail, name='detail'),
]
