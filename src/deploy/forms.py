# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-22
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django import forms


class ReleaseForm(forms.Form):
    project = forms.CharField(help_text='项目')
    env = forms.CharField(help_text='环境')
    comment = forms.CharField(help_text='发布说明')
