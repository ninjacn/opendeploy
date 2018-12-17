# -*- coding: utf-8 -*-
# Author: Pengming Yao<x@ninjacn.com>
# Date created: 2018-12-16

from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views
from opendeploy import settings

app_name='accounts'

urlpatterns = [
    url(r'^login/$', views.login, name='login'),
    url(r'^profile/$', views.profile, name='profile'),
    url(r'^register/$', views.register, name='register'),
    url(r'^logout/$', auth_views.logout, {'next_page': settings.LOGIN_REDIRECT_URL}, name='logout'),
    url(r'^change-password/$', views.change_password, name='change_password'),
]
