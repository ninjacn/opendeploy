# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-23
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import io
import os
import requests
import subprocess
import pexpect
import json
import smtplib
import logging

from django.core.mail.backends.smtp import EmailBackend
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from opendeploy import settings
from deploy.models import Task, TaskHostRela
from setting.services import SettingService

class DingdingService():

    def __init__(self):
        pass

    '''
    e.g.
    dingdingService = DingdingService()
    url = 'https://oapi.dingtalk.com/robot/send?access_token=xx'
    dingdingService.send_chat_robot(url, 1)
    '''
    def send_chat_robot(self, url, tid, start=True, rollback=False):
        settingService = SettingService()
        site_url = settingService.get_site_url()
        try:
            task = Task.objects.get(id=tid)
            task_url = site_url + reverse('deploy:detail', args=[tid])
        except:
            return False

        def get_status_display(status, status_choices):
            for item in status_choices:
                if item[0] == status:
                    return item[1]
        status_str = ''
        if start:
            if rollback:
                status_str = '开始回滚'
            else:
                status_str = '开始发布'
        else:
            if rollback:
                status_str = '回滚结束 - ' + get_status_display(task.status_rollback, Task.STATUS_ROLLBACK_CHOICES)
            else:
                status_str = '发布结束 - ' + get_status_display(task.status, Task.STATUS_CHOICES)

        data = {
            'msgtype': 'markdown',
            'markdown': {
                'title': 'Opendeploy',
                'text': "Opendeploy\n\n #" + str(tid) + ' 项目:' + task.project.name + \
                        "\n\n发布说明:" + task.comment + "\n\n" + status_str + "  [任务详情](" + task_url + ")",
            },
        }
        r = requests.post(url, json=data, timeout = 5).json()
        if r['errcode'] > 0:
            return False
        return True


class CommandService():
    def __init__(self, command):
        self.command = command
        self.run_script()

    def pre_process_output(self, output):
        res = []
        output=str(output)
        if len(output) > 0:
            res=output.split("\\n")
        return res

    def run_script(self):
        completed = subprocess.run(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.returncode = completed.returncode
        self.stdout = str(completed.stdout)
        self.stdout_as_list = self.pre_process_output(completed.stdout)
        self.stderr = str(completed.stderr)
        self.stderr_as_list = self.pre_process_output(completed.stderr)


'''
ssh自动认证的前提:
1、root用户
2、key名: id_rsa
'''
def ssh_connect(host, user, password):
    user = 'root'
    ssh_prefix = 'ssh -o StrictHostKeyChecking=no -o userknownhostsfile=/dev/null -o passwordauthentication=no '
    command = ssh_prefix + user + '@' + host + ' echo ping'
    commandService = CommandService(command)
    if commandService.returncode == 0:
        return True

    ssh_newkey = r'Are you sure you want to continue connecting \(yes/no\)\?'
    command_prompt = '[root@'
    terminal_prompt = r'Terminal type\?'
    terminal_type = 'vt100'

    command = 'ssh-copy-id -i ~/.ssh/id_rsa ' + user + '@' + host
    child = pexpect.spawn(command)
    try:
        i = child.expect([pexpect.TIMEOUT, ssh_newkey, '[Pp]assword: '])
        print(i)
        if i == 0: # Timeout
            return False
        if i == 1: # SSH does not have the public key. Just accept it.
            child.sendline ('yes')
            child.expect ('[Pp]assword: ')
        child.sendline(password)
        i = child.expect (['Permission denied', terminal_prompt, command_prompt])
        if i == 0:
            return False
        if i == 1:
            # child.sendline (terminal_type)
            child.expect (command_prompt)
            child.sendline ('exit')
            return True
        if child == None:
            return False
        else:
            child.sendline ('exit')
            return False
    except pexpect.exceptions.EOF:
        print('sss')
        return True
    except:
        return False


# 处理webhook请求正文
class WebhookRequestBody():

    def __init__(self, request):
        try:
            self.body = json.loads(request.body)
            self.request = request
        except:
            raise RuntimeError('POST数据校验不正确，请确认为Json格式')

    def get_body(self):
        return self.body

    def get_urls(self):
        return []



class WebhookRequestBodyOfGitlabService(WebhookRequestBody):

    def get_event_name(self):
        return self.body['object_kind']

    def get_branch_name(self):
        try:
            if self.get_event_name() == 'push':
                return self.body['ref'].split("/")[2]
            elif (self.get_event_name() == 'merge_request') and (self.body['object_attributes']['state'] == 'merged'):
                return self.body['object_attributes']['target_branch']
        except:
            return 'master'

    def get_comment(self):
        try:
            if self.get_event_name() == 'push':
                return self.body['commits'][0]['message'] + ' ' + self.body['user_name'] + ' ' + self.body['checkout_sha']
            elif (self.get_event_name() == 'merge_request') and (self.body['object_attributes']['state'] == 'merged'):
                return self.body['object_attributes']['last_commit']['author']['name'] + ' ' + \
                        self.body['object_attributes']['last_commit']['id'] + ' ' + \
                        self.body['object_attributes']['last_commit']['message']
        except:
            return ''

    def get_urls(self):
        return [self.body['repository']['git_ssh_url'], self.body['repository']['git_http_url']]



class WebhookRequestBodyOfGithubService(WebhookRequestBody):
    def get_event_name(self):
        try:
            return self.request.META['X-GitHub-Event']
        except:
            pass

    def get_branch_name(self):
        try:
            if self.get_event_name() == 'push':
                return self.body['ref'].split("/")[2]
        except:
            pass
        return 'master'

    def get_comment(self):
        try:
            return self.body['head_commit']['message'] + ' ' + self.body['head_commit']['author']['name'] + ' ' + \
                    self.body['head_commit']['id']
        except:
            return ''

    def get_urls(self):
        return [self.body['repository']['ssh_url'], self.body['repository']['url']]


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
                password=mail_info.password, use_tls=use_tls, timeout=30)

    def send_mail(self, tid, rollback=False):
        def get_status_display(status, status_choices):
            for item in status_choices:
                if item[0] == status:
                    return item[1]
        try:
            task = Task.objects.get(id=tid)
        except:
            raise RuntimeError('任务不存在')
        taskHostRela = TaskHostRela.objects.filter(task=task)
        settingService = SettingService()
        site_url = settingService.get_site_url()
        task_url = site_url + reverse('deploy:detail', args=[tid])
        status_str = ''
        if rollback:
            status_str = get_status_display(task.status_rollback, Task.STATUS_ROLLBACK_CHOICES)
        else:
            status_str = get_status_display(task.status, Task.STATUS_CHOICES)
        subject = status_str + ' #' + str(task.id) + ' [' + task.project.name + ']'
        to_list = []
        if task.creater.email:
            to_list.append(task.creater.email)
        else:
            raise RuntimeError('邮件为空')
        if rollback:
            log_filename = str(tid) + '_rollback.log'
        else:
            log_filename = str(tid) + '.log'
        log_path = os.path.join(settings.RELEASE_LOG_PATH[0], log_filename)
        log_body = ''
        attach = []
        try:
            with open(log_path, 'r') as f:
                log_body = f.read()
            attach.append({'body': log_body}) 
        except:
            pass
        body = render_to_string('emails/release.html', {
            'task': task,
            'taskHostRela': taskHostRela,
            'url': task_url,
            'rollback': rollback,
        })
        return self.send(to_list, subject, body, attach)

    def send(self, to, subject, body, attach=[]):
        msg = EmailMultiAlternatives(subject, body, self.from_email, to, connection=self.backend)
        msg.attach_alternative(body, "text/html")
        if attach:
            for item in attach:
                msg.attach('详情日志.log', item['body'], 'text/plain')
        try:
            msg.send()
        except smtplib.SMTPAuthenticationError as e:
            self.err_msg = e
        except smtplib.SMTPException as e:
            self.err_msg = e
        except:
            self.err_msg = '未知错误'
        if self.err_msg:
            print('邮件发送失败:' + str(self.err_msg))
        return False

