# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.core.validators import validate_ipv4_address
from django.contrib.auth.models import User
from django.db.models import Q
from django import forms

from cmdb.models import Host
from setting.models import SettingMail, SettingGeneral, SettingPublicCloud
import re


class AddEnvForm(forms.Form):
    name = forms.CharField()
    comment = forms.CharField(required=False)

class AddHostForm(forms.Form):
    ipaddr = forms.CharField(validators=[validate_ipv4_address],)
    provider = forms.CharField()
    hostname = forms.CharField(required=False)
    root_password = forms.CharField(required=False)
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

class SettingGeneralForm(forms.ModelForm):

    class Meta:
        model = SettingGeneral
        fields = ['enable_register',]

class SettingPublicCloudForm(forms.ModelForm):

    class Meta:
        model = SettingPublicCloud
        fields = ['aliyun_access_key_id', 'aliyun_access_key_secret', 'qcloud_secret_id', \
                'qcloud_secret_key',]

class SettingMailForm(forms.ModelForm):
    class Meta:
        model = SettingMail
        fields = ['from_email', 'host', 'port', 'username', \
                'password', 'use_tls']

class UserAddForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField()
    first_name = forms.CharField()
    is_superuser = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False)
    password = forms.CharField(min_length=6, max_length=16, help_text='密码')

    def clean(self):
        cleaned_data = super(UserAddForm, self).clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        try:
            user = User.objects.get(email=email)
            self.add_error('email', email + ' - 该邮箱已经存在')
        except:
            pass

class UserEditForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField()
    first_name = forms.CharField()
    is_superuser = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(UserEditForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(UserEditForm, self).clean()
        email = cleaned_data.get('email')

        user = User.objects.filter(~Q(id=self.user.id) & Q(email=email))
        if user:
            self.add_error('email', email + ' - 该邮箱已经存在')

# 从公有云导入
class ImportFromPublicCloudForm(forms.Form):
    provider = forms.CharField()
    region = forms.CharField()
