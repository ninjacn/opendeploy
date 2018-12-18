# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.conf.urls import url

from admin.views import deploy, cmdb, accounts, setting

app_name = 'admin'
urlpatterns = [
    url(r'^$', deploy.project, name='homepage'),
    # accounts
    url(r'^accounts/all_users$', accounts.all_users, name='accounts.all_users'),
    url(r'^accounts/user/add$', accounts.user_add, name='accounts.user_add'),
    url(r'^accounts/user/edit/(?P<uid>\d+)$', accounts.user_edit, name='accounts.user_edit'),
    url(r'^accounts/user/del/(?P<uid>\d+)$', accounts.user_del, name='accounts.user_del'),

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
    url(r'^cmdb/import_from_public_cloud$', cmdb.import_from_public_cloud, name='cmdb.import_from_public_cloud'),
    url(r'^cmdb/get_region_list$', cmdb.get_region_list, name='cmdb.get_region_list'),
    url(r'^cmdb/import_from_public_cloud_as_api$', cmdb.import_from_public_cloud_as_api, name='cmdb.import_from_public_cloud_as_api'),

    # setting
    url(r'^setting/general$', setting.general, name='setting.general'),
    url(r'^setting/mail$', setting.mail, name='setting.mail'),
    url(r'^setting/public_cloud$', setting.public_cloud, name='setting.public_cloud'),
]
