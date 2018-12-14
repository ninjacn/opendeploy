# -*- coding: utf-8 -*-
from django.conf.urls import url

from admin.views import deploy, cmdb

app_name = 'admin'
urlpatterns = [
    url(r'^$', deploy.index, name='index'),
    # project
    url(r'^deploy/project$', deploy.project, name='deploy.project'),
    url(r'^deploy/project/add$', deploy.project_add, name='deploy.project_add'),
    url(r'^deploy/project/edit/(?P<gid>\d+)$', deploy.project_edit, name='deploy.project_edit'),
    url(r'^deploy/credential$', deploy.credential, name='deploy.credential'),
    url(r'^deploy/credential/add$', deploy.credential_add, name='deploy.credential_add'),
    url(r'^deploy/credential/edit/(?P<gid>\d+)$', deploy.credential_edit, name='deploy.credential_edit'),

    # env
    url(r'^deploy/env$', deploy.env, name='deploy.env'),
    url(r'^deploy/env/add$', deploy.env_add, name='deploy.env_add'),

    # cmdb
    url(r'^cmdb/host$', cmdb.host, name='cmdb.host'),
    url(r'^cmdb/host/add$', cmdb.host_add, name='cmdb.host_add'),
    url(r'^cmdb/host/edit/(?P<id>\d+)$', cmdb.host_edit, name='cmdb.host_edit'),
    url(r'^cmdb/hostgroup$', cmdb.hostgroup, name='cmdb.hostgroup'),
    url(r'^cmdb/hostgroup/add$', cmdb.hostgroup_add, name='cmdb.hostgroup_add'),
    url(r'^cmdb/hostgroup/edit/(?P<gid>\d+)$', cmdb.hostgroup_edit, name='cmdb.hostgroup_edit'),

    # setting
    url(r'^deploy/setting$', deploy.setting, name='setting'),
    url(r'^deploy/setting/mail$', deploy.setting_mail, name='setting_mail'),
]
