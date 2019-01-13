# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from .models import SettingMail, SettingLdap, SettingGeneral, SettingPublicCloud
from cmdb.models import Host
from opendeploy import settings

class SettingService():
    def get_mail_info(self):
        allinfo = SettingMail.objects.all()
        if allinfo:
            for info in allinfo:
                return info

    def get_public_cloud_info(self):
        allinfo = SettingPublicCloud.objects.all()
        if allinfo:
            for info in allinfo:
                return info

    def get_ldap_info(self):
        allinfo = SettingLdap.objects.all()
        if allinfo:
            for info in allinfo:
                return info

    def is_enable_register(self):
        allinfo = SettingGeneral.objects.all()
        if allinfo:
            for info in allinfo:
                return info.enable_register

    def get_general_info(self):
        allinfo = SettingGeneral.objects.all()
        if allinfo:
            for info in allinfo:
                return info

    def get_site_url(self):
        info = self.get_general_info()
        if info:
            return info.site_url
        return ''
