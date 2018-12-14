# -*- coding: utf-8 -*-
from django import forms
from cmdb.models import Host
from deploy.models import SettingMail, Setting
import re


class AddEnvForm(forms.Form):
    name = forms.CharField()
    comment = forms.CharField(required=False)

class AddHostForm(forms.Form):
    ipaddr = forms.CharField()
    hostname = forms.CharField(required=False)
    status = forms.ChoiceField(choices=Host.STATUS_CHOICES)
    comment = forms.CharField(required=False)

class AddHostGroupForm(forms.Form):
    name = forms.CharField()
    comment = forms.CharField(required=False)

class EditHostGroupForm(forms.Form):
    name = forms.CharField()
    status = forms.CharField()
    comment = forms.CharField(required=False)

class AddProjectForm(forms.Form):
    name = forms.CharField()
    vcs_type = forms.CharField()
    credential = forms.CharField()
    repository_url = forms.CharField()
    dest_rootpath = forms.CharField()
    deploy_mode = forms.CharField()
    status = forms.CharField()
    comment = forms.CharField(required=False)

# 用户名与密码认证
class AddCredentialForPasswordForm(forms.Form):
    type = forms.CharField()
    username = forms.CharField()
    password = forms.CharField()
    comment = forms.CharField(required=False)

# 用户名与私钥认证
class AddCredentialForPrivateForm(forms.Form):
    type = forms.CharField()
    username = forms.CharField()
    private_key = forms.CharField()
    comment = forms.CharField(required=False)

class SettingForm(forms.ModelForm):

    class Meta:
        model = Setting
        fields = ['enable_register',]

class SettingMailForm(forms.ModelForm):
    class Meta:
        model = SettingMail
        fields = ['from_email', 'host', 'port', 'username', \
                'password', 'use_tls']
