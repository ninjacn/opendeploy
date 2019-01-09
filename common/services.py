# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-23
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import io
import requests
import subprocess
import pexpect
import json

from deploy.models import Task


class DingdingService():

    def __init__(self):
        pass

    '''
    e.g.
    dingdingService = DingdingService()
    url = 'https://oapi.dingtalk.com/robot/send?access_token=xx'
    dingdingService.send_chat_robot(url, 1)
    '''
    def send_chat_robot(self, url, tid):
        try:
            task = Task.objects.get(id=tid)
            task_url = '/detail/12'
        except:
            return False

        data = {
            'msgtype': 'markdown',
            'markdown': {
                'title': 'Opendeploy',
                'text': "Opendeploy\n\n #" + str(tid) + ' 项目:' + task.project.name + \
                        "\n\n发布完成   [任务详情](" + task_url + ")",
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
                return self.body['user_name'] + ' ' + self.body['checkout_sha'] + ' ' + self.body['commits'][0]['message']
            elif (self.get_event_name() == 'merge_request') and (self.body['object_attributes']['state'] == 'merged'):
                return self.body['object_attributes']['last_commit']['author']['name'] + ' ' + \
                        self.body['object_attributes']['last_commit']['id'] + ' ' + \
                        self.body['object_attributes']['last_commit']['message']
        except:
            return ''



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
            return self.body['head_commit']['author']['name'] + ' ' + \
                    self.body['head_commit']['sha'] + ' ' + self.body['head_commit']['message']
        except:
            return ''
