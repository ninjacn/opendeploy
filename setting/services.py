# -*- coding: utf-8 -*-
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
