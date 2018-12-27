# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.db import models
from django.contrib.auth.models import User

from cmdb.models import HostGroup
from common.models import TimeStampedModel

class Env(TimeStampedModel):
    name = models.CharField(max_length=255,unique=True)
    comment = models.CharField(max_length=255, default='')

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'deploy_env'
        verbose_name_plural = '环境'
        verbose_name = '环境'

''' 凭据 '''
class Credentials(TimeStampedModel):
    TYPE_USER_PWD = 1
    TYPE_USER_PRIVATE_KEY = 2
    TYPE_CHOICES = (
        (TYPE_USER_PWD, '用户名和密码'),
        (TYPE_USER_PRIVATE_KEY, '用户名和私钥'),
    )
    type = models.IntegerField(default=TYPE_USER_PWD, choices=TYPE_CHOICES)
    username = models.CharField('用户名', max_length=255, default='')
    password = models.CharField('密码', max_length=255, default='')
    private_key = models.TextField('私钥', default='', help_text='')
    comment = models.CharField('备注', max_length=255, default='')

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'deploy_credentials'
        verbose_name_plural = '凭据'
        verbose_name = '凭据'

class Project(TimeStampedModel):
    STATUS_ENABLED = '1'
    STATUS_DISABLED = '0'
    STATUS_CHOICES = (
        (STATUS_ENABLED, '启用'),
        (STATUS_DISABLED, '禁用'),
    )
    TYPE_GIT = 'git'
    TYPE_SVN = 'svn'
    TYPE_CHOICES = (
        (TYPE_GIT, 'GIT'),
        (TYPE_SVN, 'SVN'),
    )

    DEPLOY_MODE_INCREMENT = '0'
    DEPLOY_MODE_ALL = '1'
    DEPLOY_MODE_CHOICES = (
        (DEPLOY_MODE_INCREMENT, '增量'),
        (DEPLOY_MODE_ALL, '全量'),
    )
    DEPLOY_MODE_CHOICES_LONG = (
        (DEPLOY_MODE_INCREMENT, '增量发布，不对目标服务器做软链'),
        (DEPLOY_MODE_ALL, '全量发布，同步所有代码到目录服务器，交做软链'),
    )
    name = models.CharField('名称', max_length=255, unique=True, null=True)
    vcs_type = models.CharField('仓库类型', max_length=255, default=TYPE_GIT, choices=TYPE_CHOICES)
    repository_url = models.CharField('仓库地址', max_length=255)
    dest_path = models.CharField('项目路径', max_length=255, default='')
    credentials = models.ForeignKey(Credentials, on_delete=models.SET_NULL, related_name='credentials', null=True )
    comment = models.CharField('备注', max_length=255, default='')
    deploy_mode = models.CharField('部署模式', max_length=2, default=DEPLOY_MODE_INCREMENT, choices=DEPLOY_MODE_CHOICES)
    status = models.CharField(max_length=2, default=STATUS_ENABLED, choices=STATUS_CHOICES)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'deploy_project'
        verbose_name_plural = '项目'
        verbose_name = '项目'

class ProjectEnvConfig(TimeStampedModel):
    # pid = models.IntegerField('项目ID', null=True, help_text='')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True)
    env = models.ForeignKey(Env, on_delete=models.SET_NULL, null=True)
    branch = models.CharField('分支名', max_length=255, default='master', null=True)
    host_group = models.ForeignKey(HostGroup, on_delete=models.SET_NULL, null=True)
    before_hook = models.TextField('发布前钩子', default='', help_text='')
    after_hook = models.TextField('发布后钩子', default='', help_text='')

    def __str__(self):
        return self.project.name + '_' + self.env.name

    class Meta:
        db_table = 'deploy_project_env_config'
        verbose_name_plural = '项目环境配置'
        verbose_name = '项目环境配置'


''' 发布任务 '''
class Task(TimeStampedModel):
    ACTION_RELEASE = '0'
    ACTION_ROLLBACK = '1'

    STATUS_RELEASE_WAIT = '0'
    STATUS_RELEASE_START = '1'
    STATUS_RELEASE_FINISH = '2'
    STATUS_RELEASE_FINISH_ERR = '3'
    STATUS_CHOICES = (
        (STATUS_RELEASE_WAIT, '待发布'),
        (STATUS_RELEASE_START, '正在发布'),
        (STATUS_RELEASE_FINISH, '发布成功'),
        (STATUS_RELEASE_FINISH_ERR, '发布失败'),
    )

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name='project', null=True )
    creater = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='user', null=True )
    env = models.ForeignKey(Env, on_delete=models.SET_NULL, related_name='env', null=True )
    has_rollback = models.CharField('有无回滚', max_length=255, default='0')
    release_host_status = models.TextField('发布主机状态', default='', help_text='')
    has_rollback = models.CharField('有无回滚', max_length=255, default='0')
    status = models.CharField('状态', max_length=16, default=STATUS_RELEASE_WAIT, choices=STATUS_CHOICES)
    comment = models.CharField('备注', max_length=255, default='')

    def __str__(self):
        return self.id

    class Meta:
        db_table = 'deploy_task'
        verbose_name_plural = '任务'
        verbose_name = '任务'

