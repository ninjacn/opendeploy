# -*- coding: utf-8 -*-
from django.conf.urls import url

from admin.views import deploy, cmdb

urlpatterns = [
    url(r'^$', deploy.index),
    # project
    url(r'^deploy/project$', deploy.project),
    url(r'^deploy/project/add$', deploy.add_project),
    url(r'^deploy/project/edit/(?P<gid>\d+)$', deploy.edit_project),
    url(r'^deploy/credential$', deploy.credential),
    url(r'^deploy/credential/add$', deploy.add_credential),
    url(r'^deploy/credential/edit/(?P<gid>\d+)$', deploy.edit_credential),

    # env
    url(r'^deploy/env$', deploy.env),
    url(r'^deploy/env/add$', deploy.env_add),

    # cmdb
    url(r'^cmdb/host$', cmdb.host),
    url(r'^cmdb/host/add$', cmdb.add_host),
    url(r'^cmdb/host/edit/(?P<id>\d+)$', cmdb.edit_host),
    url(r'^cmdb/hostgroup$', cmdb.hostgroup),
    url(r'^cmdb/hostgroup/add$', cmdb.add_hostgroup),
    url(r'^cmdb/hostgroup/edit/(?P<gid>\d+)$', cmdb.edit_hostgroup),

    # setting
    url(r'^deploy/setting$', deploy.setting),
    url(r'^deploy/setting/mail$', deploy.setting_mail),
]
