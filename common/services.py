# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-23
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import requests

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

