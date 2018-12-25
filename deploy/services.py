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
import subprocess
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
from opendeploy import settings
from setting.services import SettingService


class CommandService():
    def __init__(self, command):
        self.command = command

    def run_script(self):
        completed = subprocess.run(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.returncode = completed.returncode
        self.stdout = completed.stdout
        self.stderr = completed.stderr

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

class DeployService():
    def __init__(self, tid, action=Task.ACTION_RELEASE):
        self.tid = tid
        try:
            self.task = Task.objects.get(id=self.tid)
        except:
            raise RuntimeError('任务不存在')

        self.myLoggingService = MyLoggingService(self.tid, action)
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
        self.action = action
        self.project_obj = ProjectService(self.pid)
        self.project = self.project_obj.get()
        self.deploy_mode = self.project.deploy_mode
        self.config = self.project_obj.get_config(self.env_id)
        self.myLoggingService.info('repository_url:' + self.project.repository_url)
        self.myLoggingService.info('环境:' + self.task.env.name)
        if self.project.vcs_type == Project.TYPE_GIT:
            self.branch = self.config.branch

        self.all_host = self.project_obj.get_all_host(self.env_id)
        if not self.all_host:
            self.myLoggingService.info('主机列表为空')
            raise RuntimeError('主机列表为空')
            
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
        self.myLoggingService.info('开始检出仓库')
        if self.vcs.checkout() is not True:
            self.myLoggingService.error(self.vcs.checkout_errmsg)
            raise RuntimeError(self.vcs.checkout_errmsg)
        self.myLoggingService.info('检出仓库完成')

        if self.action == Task.ACTION_RELEASE:
            # before_release hook, 不同环境对应不同的hook
            self.release()
            # after_release
        # rollback
        elif self.action == Task.ACTION_ROLLBACK:
            self.rollback()
        else:
            self.myLoggingService.error('执行动作异常')
            raise RuntimeError('执行动作异常')


    def release(self):
        task_id = 100
        for host in self.all_host:
            if self.deploy_mode == Project.DEPLOY_MODE_ALL:
                command = self.rsync_prefix + self.rsync_exclude_parms + self.working_dir + '/ ' + \
                        host + ':' + self.project.dest_path + '_' + str(task_id)
            elif self.deploy_mode == Project.DEPLOY_MODE_INCREMENT:
                command = self.rsync_prefix + self.rsync_exclude_parms + self.working_dir + '/ ' + \
                        host + ':' + self.project.dest_path
            else:
                RuntimeError('模式不可用')
            print(command)
            commandService = CommandService(command)
            commandService.run_script()
            print(commandService.returncode)
            print(commandService.stdout)
            print(commandService.stderr)
            if commandService.returncode > 0:
                continue
            # add link
            if self.deploy_mode == Project.DEPLOY_MODE_ALL:
                pass

        def rollback(self):
            pass

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
            file_path = os.path.join(settings.RELEASE_LOG_PATH[0], filename)
            handler = logging.FileHandler(file_path, 'w')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        else:
            raise RuntimeError('任务ID不能为空')
    
    def info(self, msg):
        self.logger.info(msg)

    def error(self, msg):
        self.logger.error(msg)
