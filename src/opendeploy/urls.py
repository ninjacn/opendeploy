# -*- coding: utf-8 -*-
# Author: Pengming Yao<x@ninjacn.com>
# Date created: 2018-12-16

from django.conf.urls import include, url
from opendeploy import settings
from django.conf.urls.static import static
from deploy.views import test

urlpatterns = [
    url(r'^', include('deploy.urls')),
    url(r'^test', test),
    url(r'^accounts/', include('accounts.urls')),
    url(r'^admin/', include('admin.urls')),
    url(r'^api/', include('api.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_URL)
