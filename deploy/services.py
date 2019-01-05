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

from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from deploy.models import Project, ProjectEnvConfig, Env, Credentials, Task
from cmdb.models import Host
from deploy.models import TaskHostRela
from opendeploy import settings
from setting.services import SettingService
from common.services import CommandService


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

        if kwargs['auth_type'] is None:
            self.auth_type = Credentials.TYPE_USER_PRIVATE_KEY
        else:
            self.auth_type = kwargs['auth_type']

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
        git_ssh_cmd = ''
        if self.auth_type == Credentials.TYPE_USER_PRIVATE_KEY:
            git_ssh_cmd = 'ssh -i %s' % self.private_key_path

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
                self.repo.run_command('cleanup', ['--remove-unversioned', '--remove-ignored', '--vacuum-pristines'])
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

class ProjectService(object):
    # def __new__(cls, id):
        # super(ProjectService, cls).__new__(cls)

    def __init__(self, id=None):
        if id:
            self.id = id
            try:
                self.project = Project.objects.get(id=self.id)
            except:
                raise RuntimeError('项目不存在。')

    def get_valid_all(self):
        return Project.objects.filter(status=Project.STATUS_ENABLED)

    def get(self):
        return self.project

    def get_all_host(self, env_id=None, type='ip'):
        try:
            env = Env.objects.get(id=env_id)
            config = self.get_config(env_id)
            hosts = []
            for item in config.host_group.host.filter(status=Host.STATUS_ENABLED):
                if type == 'ip':
                    hosts.append(item.ipaddr)
                elif type == 'hostname':
                    hosts.append(item.hostname)
                else:
                    hosts.append(item.ipaddr)
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
            return self.project.dest_path + '_' + str(self.id)
        elif self.project.deploy_mode == Project.DEPLOY_MODE_INCREMENT:
            return self.project.dest_path

    # 获取回滚路径
    def get_rollback_path(self):
        if self.project.deploy_mode == Project.DEPLOY_MODE_ALL:
            '''
            哪个版本正常就回滚哪个。最新的任务是不能回滚的。
            '''
            return self.project.dest_path + '_release_' + str(self.id)
        elif self.project.deploy_mode == Project.DEPLOY_MODE_INCREMENT:
            return self.project.dest_path + '_rollback_' + str(self.id)

    def exec_hook_before_release(self):
        before_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/before_hook_' + str(self.projectEnvConfig.id))
        if os.path.exists(before_hook_path):
            commandService = CommandService(before_hook_path)
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

    def exec_hook_after_release(self):
        after_hook_path = os.path.join(settings.BASE_DIR, 'storage/hooks/after_hook_' + str(self.projectEnvConfig.id))
        if os.path.exists(after_hook_path):
            commandService = CommandService(after_hook_path)
            self.myLoggingService.info('检测到发布前Hook, 准备执行:')
            self.myLoggingService.info('command:' + after_hook_path)
            with open(after_hook_path) as f:
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



class DeployService():
    def __init__(self, tid, action=Task.ACTION_RELEASE):
        self.tid = tid
        self.action = action
        self.myLoggingService = MyLoggingService(self.tid, action)
        self.taskService = TaskService(self.tid, self.myLoggingService)
        self.task = self.taskService.task
        if self.action == Task.ACTION_RELEASE:
            if self.task.status in [Task.STATUS_RELEASE_FINISH, Task.STATUS_RELEASE_FINISH_ERR]:
                raise RuntimeError('任务已发布，退出.')
        elif self.action == Task.ACTION_ROLLBACK:
            if self.task.status_rollback in [Task.STATUS_ROLLBACK_FINISH, Task.STATUS_ROLLBACK_FINISH_ERR]:
                raise RuntimeError('任务已回滚，退出.')

        self.myLoggingService.info('准备初始化工作区')

        self.workspace_path = os.path.expanduser(settings.WORKSPACE_PATH)
        if os.path.exists(self.workspace_path) == False:
            os.makedirs(self.workspace_path)

        self.myLoggingService.info('初始化工作区完成')

        self.rsync_prefix = 'rsync -e "ssh -o StrictHostKeyChecking=no -o userknownhostsfile=/dev/null -o passwordauthentication=no" -rlptDKv '
        self.rsync_exclude_parms = ' --exclude=.git/ --exclude=.svn/ '

        self.ssh_prefix = 'ssh -o StrictHostKeyChecking=no -o userknownhostsfile=/dev/null -o passwordauthentication=no '

        self.pid = self.task.project.id
        self.env_id = self.task.env.id
        self.project_obj = ProjectService(self.pid)
        self.project = self.project_obj.get()
        self.deploy_mode = self.project.deploy_mode
        self.config = self.project_obj.get_config(self.env_id)
        if self.deploy_mode not in [Project.DEPLOY_MODE_ALL, Project.DEPLOY_MODE_INCREMENT] :
            self.myLoggingService.info('模式不可用, 请检查项目配置')
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

        self.all_host = self.project_obj.get_all_host(self.env_id)
        if not self.all_host:
            self.myLoggingService.info('主机列表为空, 请在后台进行配置')
            raise RuntimeError('主机列表为空, 请在后台进行配置')
            
        self.myLoggingService.info('主机列表:' + (','.join(self.all_host)))

        self.myLoggingService.info('初始化仓库')
        if self.project.vcs_type == Project.TYPE_GIT:
            self.working_dir = os.path.join(self.workspace_path, str(self.pid) \
                    + "_" + self.branch)
            self.myLoggingService.info('工作区路径:' + self.working_dir)
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
            self.working_dir = os.path.join(self.workspace_path, str(self.pid)) 
            self.vcs = SvnService(self.project.repository_url, self.working_dir, 
                    username=self.project.credentials.username, 
                    password=self.project.credentials.password)

        self.myLoggingService.info('初始化仓库完成')


    def run(self):
        if self.action == Task.ACTION_RELEASE:
            self.myLoggingService.info('开始检出仓库')
            if self.vcs.checkout() is not True:
                self.myLoggingService.error(self.vcs.checkout_errmsg)
                raise RuntimeError(self.vcs.checkout_errmsg)
            self.myLoggingService.info('检出仓库完成')

            # before hook
            if self.taskService.exec_hook_before_release():
                self.myLoggingService.info('发布前调用钩子成功')
            else:
                self.myLoggingService.error('发布前调用钩子失败')
                raise RuntimeError('发布前调用钩子失败')

            self.release()
        # rollback
        elif self.action == Task.ACTION_ROLLBACK:
            self.rollback()


    def release(self):
        errno=0
        for host in self.all_host:
            self.myLoggingService.info('开始发布主机, host:' + host)
            if self.deploy_mode == Project.DEPLOY_MODE_ALL:
                command = self.rsync_prefix + self.rsync_exclude_parms + self.working_dir + '/ ' + \
                        host + ':' + self.taskService.get_release_path()
            elif self.deploy_mode == Project.DEPLOY_MODE_INCREMENT:
                command = self.rsync_prefix + self.rsync_exclude_parms + self.working_dir + '/ ' + \
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
                #标记主机状态
                taskHostRela = TaskHostRela()
                taskHostRela.host=host
                taskHostRela.task=self.task
                taskHostRela.status_release=TaskHostRela.STATUS_RELEASE_ERROR
                taskHostRela.save()
                continue
            else:
                self.myLoggingService.info('同步正常, host:' + host)
                if len(commandService.stdout_as_list) > 0:
                    self.myLoggingService.info('脚本输出:')
                    for line in commandService.stdout_as_list:
                        self.myLoggingService.info(line)

                # after hook
                if self.taskService.exec_hook_after_release():
                    status_release=TaskHostRela.STATUS_RELEASE_SUCCESS
                    self.myLoggingService.info('发布后调用钩子成功')
                else:
                    status_release=TaskHostRela.STATUS_RELEASE_ERROR
                    self.myLoggingService.error('发布后调用钩子失败')

            # add link
            if self.deploy_mode == Project.DEPLOY_MODE_ALL:
                pass
            #标记主机状态
            taskHostRela = TaskHostRela()
            taskHostRela.task=self.task
            taskHostRela.host=host
            taskHostRela.status_release=status_release
            taskHostRela.save()
        if errno > 0:
            self.task.status=Task.STATUS_RELEASE_FINISH_ERR
            self.myLoggingService.info('发布结束，有异常情况')
        else:
            self.task.status=Task.STATUS_RELEASE_FINISH
            self.myLoggingService.info('发布成功')
        self.task.save()


    def rollback(self):
        errno=0
        for host in self.all_host:
            self.myLoggingService.info('开始回滚主机, host:' + host)
            if self.deploy_mode == Project.DEPLOY_MODE_ALL:
                pass
            elif self.deploy_mode == Project.DEPLOY_MODE_INCREMENT:
                command = self.ssh_prefix + host + " '" + self.rsync_prefix + self.rsync_exclude_parms + self.taskService.get_rollback_path() + \
                        ' ' + self.taskService.get_release_path() + "'"
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
                continue
            else:
                self.myLoggingService.info('回滚正常, host:' + host)
                if len(commandService.stdout_as_list) > 0:
                    self.myLoggingService.info('脚本输出:')
                    for line in commandService.stdout_as_list:
                        self.myLoggingService.info(line)
                # after hook
                if self.taskService.exec_hook_after_release():
                    status_rollback=TaskHostRela.STATUS_ROLLBACK_FINISH
                    self.myLoggingService.info('回滚后调用钩子成功')
                else:
                    status_rollback=TaskHostRela.STATUS_ROLLBACK_FINISH_ERR
                    self.myLoggingService.error('回滚后调用钩子失败')


class EnvService():

    def get_all(self):
        return Env.objects.all()

class MailService():
    def __init__(self):
        settingService = SettingService()
        mail_info = settingService.get_mail_info()
        self.from_email = mail_info.from_email
        if mail_info.use_tls:
            use_tls = True
        else:
            use_tls = False
        self.backend = EmailBackend(host=mail_info.host, port=mail_info.port, username=mail_info.username, \
                password=mail_info.password, use_tls=use_tls, timeout=10)

    def send_mail(self):
        subject, to = 'test', 'x@ninjacn.com'
        # body = render_to_string('deploy/index.html', {
        # })
        body = "hello world"
        msg = EmailMultiAlternatives(subject, body, self.from_email, [to], connection=self.backend)
        msg.attach_alternative(body, "text/html")
        return msg.send()

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
