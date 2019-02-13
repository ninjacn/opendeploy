# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django import forms
import re
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db.models import Q

class RegisterForm(forms.Form):
    username = forms.CharField(min_length=3, max_length=32, help_text='登录用户名')
    email = forms.EmailField(min_length=3, max_length=32, help_text='邮箱')
    first_name = forms.CharField(min_length=2, max_length=16, help_text='姓名或昵称')
    password1 = forms.CharField(min_length=6, max_length=16, help_text='密码')
    password2 = forms.CharField(min_length=6, max_length=16, help_text='密码确认')

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()
        username = cleaned_data.get('username')
        email = cleaned_data.get('email')
        try:
            # user = User.objects.get(Q(username=username) | Q(email=email))
            user = User.objects.get(username=username)
            self.add_error('username', username + ' - 该用户名已经存在')
        except:
            pass

        try:
            user = User.objects.get(email=email)
            self.add_error('email', email + ' - 该邮箱已经存在')
        except:
            pass

        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 is None:
            password1 = ''
        if password2 is None:
            password2 = ''

        if password1 != password2:
            self.add_error('password2', '密码两次不匹配')

class LoginForm(forms.Form):
    username = forms.CharField(min_length=3, max_length=32, help_text='登录用户名')
    password = forms.CharField(min_length=6, max_length=16, help_text='密码')

class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(min_length=6, max_length=16, help_text='当前密码')
    new_password1 = forms.CharField(min_length=6, max_length=16, help_text='新密码')
    new_password2 = forms.CharField(help_text='新密码确认',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(ChangePasswordForm, self).__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        if new_password1 is None:
            new_password1 = ''
        if new_password2 is None:
            new_password2 = ''

        if new_password1 != new_password2:
            self.add_error('new_password2', '新密码两次不匹配')

        old_password = cleaned_data.get('old_password')
        user = authenticate(username=self.user.username, password=old_password)
        if user is None:
            self.add_error('old_password', '当前密码错误')

class ForgetPasswordSendMailForm(forms.Form):
    email = forms.EmailField()

    def clean(self):
        cleaned_data = super(ForgetPasswordSendMailForm, self).clean()
        email = cleaned_data.get('email')

        result = User.objects.filter(email=email)
        if not result:
            self.add_error('email', email + u' 邮箱不存在')

class ForgetPasswordResetForm(forms.Form):
    new_password1 = forms.CharField(min_length=8, max_length=16)
    new_password2 = forms.CharField()
    token = forms.CharField()

    def clean(self):
        cleaned_data = super(ForgetPasswordResetForm, self).clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 is None:
            password1 = ''
        if password2 is None:
            password2 = ''

        if password1 != password2:
            self.add_error('password2', '密码两次不匹配')

class ChangeProfileForm(forms.Form):
    username = forms.CharField()
    email = forms.EmailField(required=False)
    first_name = forms.CharField()
    # mobile = forms.CharField(required=False, min_length=11, max_length=11)
    # dingding = forms.CharField(required=False)

