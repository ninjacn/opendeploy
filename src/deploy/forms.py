# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-22
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django import forms
from deploy.models import Task
from deploy.services import ProjectService


class ReleaseForm(forms.Form):
    project = forms.CharField(help_text='项目')
    env = forms.CharField(help_text='环境')
    comment = forms.CharField(help_text='发布说明')
    scope = forms.CharField(required=False)
    files_list = forms.CharField(required=False)

    def clean(self):
        cleaned_data = super(ReleaseForm, self).clean()
        scope = cleaned_data.get('scope')
        files_list = cleaned_data.get('files_list')
        # 检查该项目下是否有任务在进行中
        pid = cleaned_data.get('project')
        tasks = Task.objects.filter(project=ProjectService(pid).project, status__in=[
            Task.STATUS_RELEASE_WAIT,
            Task.STATUS_RELEASE_START,
        ])
        if len(tasks) > 0:
            self.add_error('project', '该项目有任务正在等待执行, 请稍候再试！')
            for task in tasks:
                if task.status == Task.STATUS_RELEASE_WAIT:
                    self.add_error('project', '任务ID:' + str(task.id) + '正在等待执行！')
                elif task.status == Task.STATUS_RELEASE_START:
                    self.add_error('project', '任务ID:' + str(task.id) + '正在执行！')
        if scope:
            if len(files_list) <= 0:
                self.add_error('files_list', '文件列表不能为空！')
