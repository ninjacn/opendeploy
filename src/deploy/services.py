# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import os
import sys
import time
import logging
from urllib.parse import urlparse

from git import Repo
from git import Git
from git.exc import GitCommandError
import svn.remote
import svn.local
from svn.exception import SvnException

from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.core.cache import cache

from deploy.models import Project, ProjectEnvConfig, Env, Credentials, Task
from cmdb.models import Host
from deploy.models import TaskHostRela, Task
from opendeploy import settings
from setting.services import SettingService
from common.services import CommandService, DingdingService, MailService


RSYNC_PREFIX = 'rsync -e "ssh -o StrictHostKeyChecking=no -o userknownhostsfile=/dev/null -o passwordauthentication=no" -rlptDv '
RSYNC_EXCLUDE_PARMS = ' --exclude=.git/ --exclude=.svn/ '
SSH_PREFIX = 'ssh -o StrictHostKeyChecking=no -o userknownhostsfile=/dev/null -o passwordauthentication=no '

def send_notify(tid, rollback=False):
    try:
        task = Task.objects.get(id=tid)
        if task.project.enable_mail_notify:
            mailService = MailService()
            mailService.send_mail(tid, rollback)
    except:
        pass

    try:
        if task.project.dingding_robot_webhook:
            dingdingService = DingdingService()    
            dingdingService.send_chat_robot(task.project.dingding_robot_webhook, tid, rollback)
    except:
        pass


class VcsServiceBase:
    def __init__(self, url, working_dir, myLoggingService):
        self.url = url
        self.working_dir = working_dir
        self.myLoggingService = myLoggingService

class GitService(VcsServiceBase):

    def __init__(self, url, working_dir, myLoggingService, **kwargs):
        VcsServiceBase.__init__(self, url, working_dir, myLoggingService)
        self.repo = None
        self.branch = kwargs['branch']

        try:
            self.auth_type = kwargs['auth_type']
        except:
            self.auth_type = None

        u = urlparse(url)
        # 转换url，添加用户名和密码
        if u.scheme in ['http', 'https'] and self.auth_type == Credentials.TYPE_USER_PWD:
            self.url = u.scheme + '://' + kwargs['username'] + ':' + kwargs['password'] + '@' \
                    + u.netloc + u.path

        if self.auth_type == Credentials.TYPE_USER_PRIVATE_KEY:
            self.private_key_path = kwargs['private_key_path']
            if os.path.exists(self.private_key_path) == False:
                self.myLoggingService.error('私钥不存在:' + self.private_key_path)
                raise RuntimeError('私钥不存在:' + self.private_key_path)


    def checkout(self):
        # git version >= 2.3
        git_ssh_cmd = 'ssh'
        if self.auth_type == Credentials.TYPE_USER_PRIVATE_KEY:
            git_ssh_cmd = 'ssh -o StrictHostKeyChecking=no -o userknownhostsfile=/dev/null -i %s' % self.private_key_path

        if os.path.isdir(self.working_dir):
            self.myLoggingService.info('工作区已存在，开始更新...')
            repo = Repo(self.working_dir)
            with repo.git.custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                try:
                    # clean workspace
                    repo.head.reset(index=True, working_tree=True)
                    if repo.untracked_files:
                        for f in repo.untracked_files:
                            tmp_path = self.working_dir + '/' +f 
                            if os.path.exists(tmp_path):
                                os.remove(tmp_path)
                    repo.remotes.origin.pull()
                except GitCommandError as e:
                    self.checkout_errmsg = e
                    return False
                except:
                    self.checkout_errmsg = "系统异常:未知原因"
                    return False
            self.myLoggingService.info('更新工作区完成')
        else:
            self.myLoggingService.info('工作区不存在，开始克隆...')
            try:
                repo = Repo.clone_from(self.url, self.working_dir, branch=self.branch, env={'GIT_SSH_COMMAND': git_ssh_cmd})
            except GitCommandError as e:
                self.checkout_errmsg = e
                return False
            except:
                self.checkout_errmsg = "系统异常:未知原因"
                return False
            self.myLoggingService.info('克隆工作区完成')
        self.repo = repo
        return True

    def get_branch(self):
        if self.repo:
            return self.repo.active_branch

    def get_commit(self):
        if self.repo:
            return self.repo.active_branch.commit

    def get_commit_message(self):
        if self.repo:
            return self.repo.active_branch.commit.message

    def get_commit_committed_date(self, format="%a, %d %b %Y %H:%M"):
        if self.repo:
            return time.strftime("%a, %d %b %Y %H:%M", time.gmtime(self.repo.active_branch.commit.committed_date))

    def get_commit_author(self):
        if self.repo:
            return {
                'name': self.repo.active_branch.commit.author.name,
                'email': self.repo.active_branch.commit.author.email,
            }

    def diff(self, commit=None):
        if self.repo:
            if commit is None:
                commit = self.repo.active_branch.commit

            diff_str = []
            for item in commit.diff('HEAD~1', create_patch=True):
                diff_str.append(str(item.diff))
            return '\n'.join(diff_str)



class SvnService(VcsServiceBase):

    def __init__(self, url, working_dir, myLoggingService, **kwargs):
        VcsServiceBase.__init__(self, url, working_dir, myLoggingService)
        self.username = kwargs['username']
        self.password = kwargs['password']

    def checkout(self):
        if os.path.isdir(self.working_dir):
            self.repo = svn.local.LocalClient(self.working_dir, 
                   username=self.username, password=self.password)
            try:
                os.chdir(self.working_dir)
                self.repo.run_command('cleanup', ['--remove-unversioned', '--remove-ignored'])
                self.repo.update()
            except SvnException as e:
                self.checkout_errmsg = e
                return False
            except:
                self.checkout_errmsg = "系统异常:未知原因"
                return False
        else:
            self.repo = svn.remote.RemoteClient(self.url, username=self.username, password=self.password)
            try:
                self.repo.checkout(self.working_dir)
            except SvnException as e:
                self.checkout_errmsg = e
                return False
            except:
                self.checkout_errmsg = "系统异常:未知原因"
                return False

        info = self.repo.info()
        self.version = info['commit_revision']
        return True


    def diff(self):
        r = svn.remote.RemoteClient(self.url, username=self.username, password=self.password)
        try:
            return r.diff(self.version-1, self.version)
        except:
            pass

    def get_commit(self):
        if self.version:
            return self.version
        return '0'

    def get_commit_message(self):
        return ''


class ProjectService(object):
    # def __new__(cls, id):
        # super(ProjectService, cls).__new__(cls)

    def __init__(self, id=None):
        if id:
            try:
                self.id = id
                self.project = Project.objects.get(id=self.id)
            except:
                raise RuntimeError('项目不存在')

    # 创建任务
    def create_task(self, env_id, creater, comment='', scope=Task.SCOPE_ALL, files_list=''):
        try:
            env = Env.objects.get(id=env_id)
        except:
            raise RuntimeError('环境不存在')
        try:
            task = Task()
            task.project = self.project
            task.env = env
            task.creater = creater
            task.comment = comment
            if scope == '1':
                task.scope = Task.SCOPE_BY_FILE
            else:
                task.scope = Task.SCOPE_ALL
            if files_list:
                task.files_list = files_list
            task.save()
            return task
        except:
            raise RuntimeError('创建任务失败')

    def get_valid_all(self):
        return Project.objects.filter(status=Project.STATUS_ENABLED)

    def get(self):
        return self.project

    def get_all_host(self, env_id=None, type='ip'):
        hosts = []
        try:
            env = Env.objects.get(id=env_id)
            config = self.get_config(env_id)
            for item in config.host_group.host.filter(status=Host.STATUS_ENABLED):
                if type == 'hostname':
                    hosts.append(item.hostname)
                else:
                    hosts.append(item.ipaddr)
            return hosts
        except:
            return []

    # 获取主机信息，包含额外信息
    def get_all_host_with_extra(self, env_id=None):
        hosts = []
        try:
            env = Env.objects.get(id=env_id)
            config = self.get_config(env_id)
            for item in config.host_group.host.filter(status=Host.STATUS_ENABLED):
                tmp = {}
                tmp['ipaddr'] = item.ipaddr
                tmp['hostname'] = item.hostname
                hosts.append(tmp)
            return hosts
        except:
            return []
    
    def get_config(self, env_id):
        try:
            env = Env.objects.get(id=env_id)
            return ProjectEnvConfig.objects.get(project=self.project, env=env)
        except:
            raise RuntimeError('项目配置不存在。')

    def get_deploy_model_label(self, mode):
        deploy_mode_choices=dict(Project.DEPLOY_MODE_CHOICES)
        try:
            return deploy_mode_choices.get(mode)
        except:
            pass


class TaskService(object):
    def __init__(self, id, myLoggingService=None):
        self.id=id
        if myLoggingService:
            self.myLoggingService=myLoggingService
        else:
            raise RuntimeError('Logger初始化失败')
        try:
            self.task=Task.objects.get(id=self.id)
            if self.task.project:
                self.project=self.task.project
            else:
                self.myLoggingService.error('项目不存在')
                raise RuntimeError('项目不存在')
        except:
            self.myLoggingService.error('任务不存在')
            raise RuntimeError('任务不存在')

        try:
            self.projectEnvConfig=ProjectEnvConfig.objects.get(project=self.project, env=self.task.env)
        except:
            self.myLoggingService.error('项目环境配置不存在')
            raise RuntimeError('项目环境配置不存在')

    # 获取发布路径
    def get_release_path(self):
        if self.project.deploy_mode == Project.DEPLOY_MODE_ALL:
            return self.project.dest_path + '_release_' + str(self.id)
        elif self.project.deploy_mode == Project.DEPLOY_MODE_INCREMENT:
            return self.project.dest_path

    # 获取项目工作区路径
    def get_workspace_path(self):
        pass


    # 获取回滚路径
    def get_rollback_path(self):
        if self.project.deploy_mode == Project.DEPLOY_MODE_ALL:
            '''
            哪个版本正常就回滚哪个。最新的任务是不能回滚的。
            '''
            return self.project.dest_path + '_release_' + str(self.id)
        elif self.project.deploy_mode == Project.DEPLOY_MODE_INCREMENT:
            return self.project.dest_path + '_rollback_' + str(self.id)

    def exec_hook_before_release(self, working_dir=None):
        try:
            before_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/before_hook_' + str(self.projectEnvConfig.id))
            if os.path.exists(before_hook_path):
                if working_dir is None:
                    working_dir = '/app'
                commandService = CommandService('cd ' + working_dir + ' && ' + before_hook_path)
                self.myLoggingService.info('检测到发布前Hook, 准备执行:')
                self.myLoggingService.info('command:' + before_hook_path)
                with open(before_hook_path) as f:
                    for line in f:
                        self.myLoggingService.info(line.strip())
                self.myLoggingService.info('exit_code:' + str(commandService.returncode))
                if commandService.returncode > 0:
                    self.myLoggingService.error('发布前hook执行异常')
                    if len(commandService.stdout) > 0:
                        self.myLoggingService.info('脚本输出:')
                        for line in commandService.stdout_as_list:
                            self.myLoggingService.error(line)
                    if len(commandService.stderr) > 0:
                        self.myLoggingService.error('脚本错误:')
                        for line in commandService.stderr_as_list:
                            self.myLoggingService.error(line)
                    return False
                else:
                    self.myLoggingService.info('发布前hook执行正常')
                    if len(commandService.stdout_as_list) > 0:
                        self.myLoggingService.info('脚本输出:')
                        for line in commandService.stdout_as_list:
                            self.myLoggingService.info(line)
                    return True
        except:
            return False

    def exec_hook_after_release(self, host):
        try:
            after_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/after_hook_' + str(self.projectEnvConfig.id))
            if os.path.exists(after_hook_path):
                self.myLoggingService.info('检测到发布后Hook, 准备执行:')
                with open(after_hook_path) as f:
                    for line in f:
                        self.myLoggingService.info(line.strip())
                # 推送脚本
                filename = 'opendeploy_hook_after_' + str(self.id) + '_' + get_random_string(30)
                remote_path = '/tmp/' + filename;
                command = RSYNC_PREFIX + after_hook_path + ' ' + host + ':' + remote_path
                self.myLoggingService.info(command)
                commandService = CommandService(command)
                if commandService.returncode > 0:
                    self.myLoggingService.error('推送脚本异常')
                    return False
                # @TODO
                self.myLoggingService.info('开始执行...')
                release_path = self.get_release_path()
                if release_path:
                    command = SSH_PREFIX + host + ' "chmod 777 ' + remote_path + ' && export OPENDEPLOY_ID=' + str(self.id) + ' && source /etc/profile && cd ' \
                         + release_path + ' && ' + remote_path + ' && ' + 'rm -f ' + remote_path + ' 2>&1"'
                else:
                    command = SSH_PREFIX + host + ' "chmod 777 ' + remote_path + ' && export OPENDEPLOY_ID=' + str(self.id) + ' && source /etc/profile && ' \
                         + remote_path + ' && ' + 'rm -f ' + remote_path + ' 2>&1"'
                self.myLoggingService.info(command)
                commandService = CommandService(command)
                self.myLoggingService.info('exit_code:' + str(commandService.returncode))
                if commandService.returncode > 0:
                    self.myLoggingService.error('发布后hook执行异常')
                    if len(commandService.stdout) > 0:
                        self.myLoggingService.info('脚本输出:')
                        for line in commandService.stdout_as_list:
                            self.myLoggingService.error(line)
                    if len(commandService.stderr) > 0:
                        self.myLoggingService.error('脚本错误:')
                        for line in commandService.stderr_as_list:
                            self.myLoggingService.error(line)
                    return False
                else:
                    self.myLoggingService.info('发布后hook执行正常')
                    if len(commandService.stdout_as_list) > 0:
                        self.myLoggingService.info('脚本输出:')
                        for line in commandService.stdout_as_list:
                            self.myLoggingService.info(line)
                    return True
        except:
            return False

    # 退出任务
    def exit_task(self, rollback=False, percent_key=None):
        if rollback:
            self.task.status_rollback=Task.STATUS_ROLLBACK_FINISH_ERR
        else:
            self.task.status=Task.STATUS_RELEASE_FINISH_ERR

        if percent_key:
            cache.set(percent_key, 100)
        self.task.save()
        send_notify(self.task.id)

    # 完成任务
    def finish_task(self, rollback=False):
        if rollback:
            self.task.status_rollback=Task.STATUS_ROLLBACK_FINISH
        else:
            self.task.status=Task.STATUS_RELEASE_FINISH
        self.task.save()



class DeployService():
    def __init__(self, tid, action=Task.ACTION_RELEASE, hosts_list=[]):
        self.tid = tid
        self.action = action
        try:
            self.task = Task.objects.get(pk=tid)
        except:
            raise RuntimeError('任务不存在，退出.')

        if self.action == Task.ACTION_RELEASE:
            if self.task.status in [Task.STATUS_RELEASE_FINISH, Task.STATUS_RELEASE_FINISH_ERR]:
                raise RuntimeError('任务已发布，退出.')
            # 状态标记
            self.task.status = Task.STATUS_RELEASE_START
            self.percent_key = 'opendeploy:percent:' + str(self.task.id)
        elif self.action == Task.ACTION_ROLLBACK:
            if self.task.status_rollback in [Task.STATUS_ROLLBACK_FINISH, Task.STATUS_ROLLBACK_FINISH_ERR]:
                raise RuntimeError('任务已回滚，退出.')
            # 状态标记
            self.task.status_rollback = Task.STATUS_ROLLBACK_START
            self.percent_key = 'opendeploy:percent:rollback:' + str(self.task.id)
        self.task.save()

        self.myLoggingService = MyLoggingService(self.tid, action)
        self.taskService = TaskService(self.tid, self.myLoggingService)
        self.myLoggingService.info('准备初始化工作区')

        self.workspace_path = os.path.expanduser(settings.WORKSPACE_PATH)
        if os.path.exists(self.workspace_path) == False:
            os.makedirs(self.workspace_path)
        self.myLoggingService.info('初始化工作区完成')
        cache.set(self.percent_key, 10)

        self.pid = self.task.project.id
        self.env_id = self.task.env.id
        self.project_obj = ProjectService(self.pid)
        self.project = self.project_obj.get()
        self.deploy_mode = self.project.deploy_mode
        self.config = self.project_obj.get_config(self.env_id)
        if self.deploy_mode not in [Project.DEPLOY_MODE_ALL, Project.DEPLOY_MODE_INCREMENT] :
            self.myLoggingService.info('模式不可用, 请检查项目配置')
            self.taskService.exit_task(percent_key=self.percent_key)
            raise RuntimeError('模式不可用, 请检查项目配置')
        self.myLoggingService.info('项目名:' + self.project.name)
        self.myLoggingService.info('仓库地址:' + self.project.repository_url)
        self.myLoggingService.info('环境:' + self.task.env.name)
        self.myLoggingService.info('部署路径:' + self.project.dest_path)
        self.myLoggingService.info('部署模式:' + self.project_obj.get_deploy_model_label(self.deploy_mode))
        if self.action == Task.ACTION_ROLLBACK:
            self.myLoggingService.info('动作: 回滚')
        else:
            self.myLoggingService.info('动作: 发布')
        if self.project.vcs_type == Project.TYPE_GIT:
            self.branch = self.config.branch

        if hosts_list:
            self.all_host = hosts_list
        else:
            self.all_host = self.project_obj.get_all_host(self.env_id)
        if not self.all_host:
            self.myLoggingService.error('主机列表为空, 请在后台进行配置')
            self.taskService.exit_task(percent_key=self.percent_key)
            raise RuntimeError('主机列表为空, 请在后台进行配置')
            
        self.myLoggingService.info('主机列表:' + (','.join(self.all_host)))
        self.myLoggingService.info('初始化仓库')
        if self.project.vcs_type == Project.TYPE_GIT:
            self.working_dir = os.path.join(self.workspace_path, str(self.pid) \
                    + "_" + self.branch)
            self.myLoggingService.info('工作区路径:' + self.working_dir)
            if self.project.credentials:
                if self.project.credentials.type == Credentials.TYPE_USER_PRIVATE_KEY:
                    private_key_path = os.path.join(settings.BASE_DIR, 'storage/privary_key/' + str(self.project.credentials.id))
                    self.myLoggingService.info('使用私钥认证')
                    self.myLoggingService.info('私钥路径:' + private_key_path)
                    self.vcs = GitService(self.project.repository_url, self.working_dir, 
                        self.myLoggingService,
                        branch=self.branch,
                        auth_type=Credentials.TYPE_USER_PRIVATE_KEY, 
                        private_key_path=private_key_path)
                else:
                    self.myLoggingService.info('使用用户名密码认证')
                    self.vcs = GitService(self.project.repository_url, self.working_dir, 
                        self.myLoggingService,
                        branch=self.branch,
                        auth_type=Credentials.TYPE_USER_PWD, username=self.project.credentials.username, 
                        password=self.project.credentials.password)
            else:
                self.myLoggingService.info('使用匿名认证')
                self.vcs = GitService(self.project.repository_url, self.working_dir, 
                    self.myLoggingService,
                    branch=self.branch
                    )
        else:
            self.working_dir = os.path.join(self.workspace_path, str(self.pid)) 
            self.myLoggingService.info('工作区路径:' + self.working_dir)
            self.vcs = SvnService(self.project.repository_url, self.working_dir, 
                    self.myLoggingService,
                    username=self.project.credentials.username, 
                    password=self.project.credentials.password)

        self.myLoggingService.info('初始化仓库完成')


    def run(self):
        if self.action == Task.ACTION_RELEASE and self.project.rsync_enable_delete:
            self.rsync_prefix = RSYNC_PREFIX + ' --delete '
        else:
            self.rsync_prefix = RSYNC_PREFIX
        if self.action == Task.ACTION_RELEASE:
            self.myLoggingService.info('开始检出仓库')
            if self.vcs.checkout() is not True:
                self.myLoggingService.error(self.vcs.checkout_errmsg)
                self.taskService.exit_task(percent_key=self.percent_key)
                raise RuntimeError(self.vcs.checkout_errmsg)
            self.myLoggingService.info('检出仓库完成')
            self.task.version = self.vcs.get_commit()
            self.task.version_message = self.vcs.get_commit_message()
            self.task.save()

            cache.set(self.percent_key, 50)

            # before hook
            res_hook_before = self.taskService.exec_hook_before_release(self.working_dir)
            if res_hook_before:
                self.myLoggingService.info('发布前调用钩子成功')
            elif res_hook_before == False:
                self.myLoggingService.error('发布前调用钩子失败')
                self.taskService.exit_task(percent_key=self.percent_key)
                raise RuntimeError('发布前调用钩子失败')
            else:
                self.myLoggingService.info('未检测到发布前钩子')

            self.release()
        # rollback
        elif self.action == Task.ACTION_ROLLBACK:
            cache.set(self.percent_key, 50)
            self.rollback()
        cache.set(self.percent_key, 100)


    def check_file_exists(self):
        return True
        if self.task.files_list:
            err_num = 0
            for item in self.task.files_list.splitlines():
                file_path = self.working_dir + '/' + item
                if os.path.exists(file_path) == False:
                    self.myLoggingService.info('文件不存在，Path:' + item)
                    err_num += 1
            if err_num == 0:
                return True
        return False

    def release(self):
        errno=0
        #检查所有文件是否在工作区存在
        if self.task.scope == Task.SCOPE_BY_FILE:
            if self.check_file_exists() == False:
                self.task.status=Task.STATUS_RELEASE_FINISH_ERR
                self.myLoggingService.error('检查文件列表路径失败，发布退出')
                self.task.save()
                send_notify(self.task.id)
                return None;
        # 从远程主机备份文件        
        if self.task.scope == Task.SCOPE_BY_FILE:
            self.myLoggingService.info('准备从远程主机备份指定文件')
            rollback_host = self.all_host[0]
            self.myLoggingService.info('备份主机地址:' + rollback_host)
            rollback_path = settings.ROLLBACK_PATH[0] + '/' + str(self.task.id)
            if os.path.exists(rollback_path) == False:
                os.mkdir(rollback_path)
            for item in self.task.files_list.splitlines():
                file_path = rollback_path + '/' + item
                command = self.rsync_prefix + RSYNC_EXCLUDE_PARMS + ' ' + \
                        rollback_host + ':' + self.taskService.get_release_path() + '/' + item + \
                        ' ' + file_path
                commandService = CommandService(command)
                if commandService.returncode > 0:
                    self.myLoggingService.error('文件备份失败, 新文件可忽略。 路径:' + item)
                    self.myLoggingService.error(command)
                    if len(commandService.stdout_as_list) > 0:
                        for line in commandService.stdout_as_list:
                            self.myLoggingService.error(line)
                    if len(commandService.stderr) > 0:
                        for line in commandService.stderr_as_list:
                            self.myLoggingService.error(line)
                else:
                    self.myLoggingService.info('文件备份成功。 路径:' + item)
        for host in self.all_host:
            single_errno=0
            self.myLoggingService.info('开始发布主机, host:' + host)
            if self.task.scope == Task.SCOPE_BY_FILE:
                for item in self.task.files_list.splitlines():
                    file_path = self.working_dir + '/' + item
                    command = self.rsync_prefix + RSYNC_EXCLUDE_PARMS + file_path + ' ' + \
                            host + ':' + self.taskService.get_release_path()
                    commandService = CommandService(command)
                    if commandService.returncode > 0:
                        self.myLoggingService.error('文件发布失败。 路径:' + item)
                        self.myLoggingService.error(command)
                        if len(commandService.stdout_as_list) > 0:
                            for line in commandService.stdout_as_list:
                                self.myLoggingService.error(line)
                        if len(commandService.stderr) > 0:
                            for line in commandService.stderr_as_list:
                                self.myLoggingService.error(line)
                        errno+=1
                        single_errno+=1
                    else:
                        self.myLoggingService.info('文件发布成功。 路径:' + item)
            else:
                if self.deploy_mode == Project.DEPLOY_MODE_ALL:
                    command = self.rsync_prefix + RSYNC_EXCLUDE_PARMS + self.working_dir + '/ ' + \
                            host + ':' + self.taskService.get_release_path()
                elif self.deploy_mode == Project.DEPLOY_MODE_INCREMENT:
                    command = self.rsync_prefix + RSYNC_EXCLUDE_PARMS + self.working_dir + '/ ' + \
                            host + ':' + self.taskService.get_release_path() + ' --backup --backup-dir=' + self.taskService.get_rollback_path()

                self.myLoggingService.info('command:' + command)
                commandService = CommandService(command)
                self.myLoggingService.info('exit_code:' + str(commandService.returncode))
                if commandService.returncode > 0:
                    self.myLoggingService.error('同步异常, host:' + host)
                    if len(commandService.stdout_as_list) > 0:
                        self.myLoggingService.error('脚本输出:')
                        for line in commandService.stdout_as_list:
                            self.myLoggingService.error(line)
                    if len(commandService.stderr) > 0:
                        self.myLoggingService.error('脚本错误:')
                        for line in commandService.stderr_as_list:
                            self.myLoggingService.error(line)
                    errno+=1
                    single_errno+=1
                    #标记主机状态
                    taskHostRela = TaskHostRela()
                    taskHostRela.host=host
                    taskHostRela.task=self.task
                    taskHostRela.status_release=TaskHostRela.STATUS_RELEASE_ERROR
                    taskHostRela.save()
                    continue
                else:
                    status_release=TaskHostRela.STATUS_RELEASE_SUCCESS
                    self.myLoggingService.info('同步正常, host:' + host)
                    if len(commandService.stdout_as_list) > 0:
                        self.myLoggingService.info('脚本输出:')
                        for line in commandService.stdout_as_list:
                            self.myLoggingService.info(line)

                    # add link
                    if self.deploy_mode == Project.DEPLOY_MODE_ALL:
                        self.myLoggingService.info('准备切换软链接...')
                        command = SSH_PREFIX + host + ' " rm -f ' + self.project.dest_path + ' && ln -s -f ' + self.taskService.get_release_path() \
                                + ' ' + self.project.dest_path + '"'
                        self.myLoggingService.info(command)
                        commandService = CommandService(command)
                        if len(commandService.stdout_as_list) > 0:
                            self.myLoggingService.info('切换软链接出错')
                            for line in commandService.stdout_as_list:
                                self.myLoggingService.info(line)
                            errno+=1
                            single_errno+=1
                            taskHostRela = TaskHostRela()
                            taskHostRela.host=host
                            taskHostRela.task=self.task
                            taskHostRela.status_release=TaskHostRela.STATUS_RELEASE_ERROR
                            taskHostRela.save()
                            continue
                        self.myLoggingService.info('切换软链接完成')

            # after hook
            res_hook_after = self.taskService.exec_hook_after_release(host)
            if res_hook_after:
                status_release=TaskHostRela.STATUS_RELEASE_SUCCESS
                self.myLoggingService.info('发布后调用钩子成功')
            elif res_hook_after == False:
                status_release=TaskHostRela.STATUS_RELEASE_ERROR
                self.myLoggingService.error('发布后调用钩子失败')
                errno+=1
                single_errno+=1
            else:
                status_release=TaskHostRela.STATUS_RELEASE_SUCCESS
                self.myLoggingService.info('未检测到发布后钩子')

            #标记主机状态
            taskHostRela = TaskHostRela()
            taskHostRela.task=self.task
            taskHostRela.host=host
            taskHostRela.status_release=status_release
            taskHostRela.save()
            if single_errno > 0:
                self.myLoggingService.error('主机发布失败，' + host)
            else:
                self.myLoggingService.info('主机发布成功，' + host)
        if errno > 0:
            self.task.status=Task.STATUS_RELEASE_FINISH_ERR
            self.myLoggingService.info('发布失败，有异常情况')
        else:
            self.task.status=Task.STATUS_RELEASE_FINISH
            self.myLoggingService.info('发布成功')
        self.task.save()
        send_notify(self.task.id)


    def rollback(self):
        errno=0
        single_errno=0
        for host in self.all_host:
            self.myLoggingService.info('开始回滚主机, host:' + host)
            if self.task.scope == Task.SCOPE_BY_FILE:
                self.myLoggingService.info('准备从发布系统回滚指定文件')
                for item in self.task.files_list.splitlines():
                    self.myLoggingService.info('回滚文件:' + item)
                    rollback_file_path = settings.ROLLBACK_PATH[0] + '/' + str(self.task.id) + '/' + item
                    command = self.rsync_prefix + RSYNC_EXCLUDE_PARMS + rollback_file_path + ' ' + \
                            host + ':' + self.taskService.get_release_path() + '/' + item
                    commandService = CommandService(command)
                    if commandService.returncode > 0:
                        self.myLoggingService.error('文件回滚失败。 路径:' + item)
                        self.myLoggingService.error(command)
                        if len(commandService.stdout_as_list) > 0:
                            for line in commandService.stdout_as_list:
                                self.myLoggingService.error(line)
                        if len(commandService.stderr) > 0:
                            for line in commandService.stderr_as_list:
                                self.myLoggingService.error(line)
                        errno+=1
                        single_errno+=1
                    else:
                        self.myLoggingService.info('文件回滚成功。 路径:' + item)
            else:
                if self.deploy_mode == Project.DEPLOY_MODE_ALL:
                    command = SSH_PREFIX + host + ' " rm -f ' + self.project.dest_path + ' && ln -s -f ' + self.taskService.get_rollback_path() \
                                + ' ' + self.project.dest_path + '"'
                elif self.deploy_mode == Project.DEPLOY_MODE_INCREMENT:
                    command = SSH_PREFIX + host + " '" + self.rsync_prefix + RSYNC_EXCLUDE_PARMS + self.taskService.get_rollback_path() + \
                            '/ ' + self.taskService.get_release_path() + "/'"
                self.myLoggingService.info('command:' + command)
                commandService = CommandService(command)
                if commandService.returncode > 0:
                    self.myLoggingService.error('回滚异常, host:' + host)
                    if len(commandService.stdout_as_list) > 0:
                        self.myLoggingService.error('脚本输出:')
                        for line in commandService.stdout_as_list:
                            self.myLoggingService.error(line)
                    if len(commandService.stderr_as_list) > 0:
                        self.myLoggingService.error('脚本错误:')
                        for line in commandService.stderr_as_list:
                            self.myLoggingService.error(line)
                    errno+=1
                    single_errno+=1
                    try:
                        taskHostRela = TaskHostRela.objects.get(host=host, task=self.task)
                    except:
                        taskHostRela = TaskHostRela(task=self.task)
                        taskHostRela.task=self.task
                        taskHostRela.host=host
                    taskHostRela.status_rollback=TaskHostRela.STATUS_ROLLBACK_ERROR
                    taskHostRela.save()
                    continue
                else:
                    status_rollback=TaskHostRela.STATUS_ROLLBACK_SUCCESS
                    self.myLoggingService.info('回滚正常, host:' + host)
                    if len(commandService.stdout_as_list) > 0:
                        self.myLoggingService.info('脚本输出:')
                        for line in commandService.stdout_as_list:
                            self.myLoggingService.info(line)
            # after hook
            res_hook_after = self.taskService.exec_hook_after_release(host) 
            if res_hook_after:
                status_rollback=TaskHostRela.STATUS_ROLLBACK_SUCCESS
                self.myLoggingService.info('回滚后调用钩子成功')
            elif res_hook_after == False:
                status_rollback=TaskHostRela.STATUS_ROLLBACK_ERROR
                self.myLoggingService.error('回滚后调用钩子失败')
                errno+=1
                single_errno+=1
            else:
                status_rollback=TaskHostRela.STATUS_ROLLBACK_SUCCESS
                self.myLoggingService.info('未检测到回滚后调用钩子')
            #标记主机状态
            try:
                taskHostRela = TaskHostRela.objects.get(host=host, task=self.task)
                taskHostRela.status_rollback=status_rollback
                taskHostRela.save()
            except:
                pass
            if single_errno > 0:
                self.myLoggingService.error('主机回滚失败，' + host)
            else:
                self.myLoggingService.info('主机回滚成功，' + host)
        if errno > 0:
            self.task.status_rollback=Task.STATUS_ROLLBACK_FINISH_ERR
            self.myLoggingService.info('回滚结束，有异常情况')
        else:
            self.task.status_rollback=Task.STATUS_ROLLBACK_FINISH
            self.myLoggingService.info('回滚成功')
        self.task.save()
        send_notify(self.task.id, rollback=True)


class EnvService():

    def get_all(self):
        return Env.objects.all()


class MyLoggingService():

    def __init__(self, tid, action=Task.ACTION_RELEASE):
        if tid:
            if action == Task.ACTION_RELEASE:
                filename = str(tid) + '.log'
            else:
                filename = str(tid) + '_rollback.log'
            self.logger = logging.getLogger(filename)
            self.logger.setLevel(logging.DEBUG)
            self.file_path = os.path.join(settings.RELEASE_LOG_PATH[0], filename)
            handler = logging.FileHandler(self.file_path, 'w')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            raise RuntimeError('任务ID不能为空')
    
    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)
