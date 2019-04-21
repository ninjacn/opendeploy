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

from cmdb.models import HostGroup, Host
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
        verbose_name_plural = '认证凭证'
        verbose_name = '认证凭证'

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
    dest_path = models.CharField('部署路径', max_length=255, default='')
    credentials = models.ForeignKey(Credentials, on_delete=models.SET_NULL, \
            related_name='credentials', null=True, blank=True)
    comment = models.CharField('备注', max_length=255, default='', null=True, blank=True)
    deploy_mode = models.CharField('部署模式', max_length=2, default=DEPLOY_MODE_INCREMENT, \
            choices=DEPLOY_MODE_CHOICES)
    dingding_robot_webhook = models.URLField('钉钉机器人webhook', max_length=255, default='', \
            null=True, blank=True)
    exclude_file = models.TextField('rsync排除文件', default='', help_text='', null=True, blank=True)
    rsync_enable_delete = models.BooleanField('启用rsync删除选项', default=False)
    enable_mail_notify = models.BooleanField('启用邮件通知', default=False)
    status = models.CharField('状态', max_length=2, default=STATUS_ENABLED, choices=STATUS_CHOICES)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'deploy_project'
        verbose_name_plural = '项目'
        verbose_name = '项目'

class ProjectEnvConfig(TimeStampedModel):
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
        indexes = [
            models.Index(fields=['project', 'env']),
        ]


''' 发布任务 '''
class Task(TimeStampedModel):
    ACTION_RELEASE = '0'
    ACTION_ROLLBACK = '1'

    STATUS_RELEASE_WAIT = 0
    STATUS_RELEASE_START = 1
    STATUS_RELEASE_FINISH = 2
    STATUS_RELEASE_FINISH_ERR = 3
    STATUS_CHOICES = (
        (STATUS_RELEASE_WAIT, '待发布'),
        (STATUS_RELEASE_START, '正在发布'),
        (STATUS_RELEASE_FINISH, '发布成功'),
        (STATUS_RELEASE_FINISH_ERR, '发布失败'),
    )

    STATUS_ROLLBACK_WAIT = 0
    STATUS_ROLLBACK_START = 1
    STATUS_ROLLBACK_FINISH = 2
    STATUS_ROLLBACK_FINISH_ERR = 3
    STATUS_ROLLBACK_CHOICES = (
        (STATUS_ROLLBACK_WAIT, '待回滚'),
        (STATUS_ROLLBACK_START, '正在回滚'),
        (STATUS_ROLLBACK_FINISH, '回滚成功'),
        (STATUS_ROLLBACK_FINISH_ERR, '回滚失败'),
    )
    SCOPE_BY_FILE = 1
    SCOPE_ALL = 0
    SCOPE_CHOICES = (
        (SCOPE_BY_FILE, '按文件列表发布'),
        (SCOPE_ALL, '全量发布'),
    )

    project = models.ForeignKey(Project, on_delete=models.SET_NULL, related_name='project', null=True )
    creater = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='user', null=True )
    env = models.ForeignKey(Env, on_delete=models.SET_NULL, related_name='env', null=True )
    status = models.IntegerField('状态', default=STATUS_RELEASE_WAIT, choices=STATUS_CHOICES)
    status_rollback = models.IntegerField('回滚状态', default=STATUS_ROLLBACK_WAIT, choices=STATUS_ROLLBACK_CHOICES)
    version = models.CharField('版本', max_length=255, default='')
    version_message = models.CharField('版本注释', max_length=255, default='')
    comment = models.CharField('备注', max_length=255, default='')
    scope = models.IntegerField('发布范围', default=SCOPE_ALL, choices=SCOPE_CHOICES)
    files_list = models.TextField('文件路径列表', max_length=255, default='', help_text='')
    celery_task_id = models.CharField('Celery Task id', max_length=255, default='')

    def __str__(self):
        return str(self.id)

    class Meta:
        db_table = 'deploy_task'
        verbose_name_plural = '任务'
        verbose_name = '任务'

class TaskHostRela(models.Model):
    STATUS_RELEASE_WAIT = 0
    STATUS_RELEASE_SUCCESS = 1
    STATUS_RELEASE_ERROR = 2
    STATUS_RELEASE_CHOICES = (
        (STATUS_RELEASE_SUCCESS, '发布成功'),
        (STATUS_RELEASE_ERROR, '发布失败'),
    )
    STATUS_ROLLBACK_WAIT = 0
    STATUS_ROLLBACK_SUCCESS = 1
    STATUS_ROLLBACK_ERROR = 2
    STATUS_ROLLBACK_CHOICES = (
        (STATUS_ROLLBACK_SUCCESS, '回滚成功'),
        (STATUS_ROLLBACK_ERROR, '回滚失败'),
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    host = models.CharField('host or ip', max_length=255, default='')
    status_release = models.IntegerField('发布状态', default=STATUS_RELEASE_WAIT, choices=STATUS_RELEASE_CHOICES)
    status_rollback = models.IntegerField('回滚状态', default=STATUS_ROLLBACK_WAIT, choices=STATUS_ROLLBACK_CHOICES)

    def __str__(self):
        return self.host

    class Meta:
        db_table = 'deploy_task_host_rela'
