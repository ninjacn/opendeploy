# -*- coding: utf-8 -*-
# Author: Pengming Yao<x@ninjacn.com>
# Date created: 2018-12-16

from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException 
from tencentcloud.cvm.v20170312 import cvm_client, models 

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

from setting.services import SettingService


class QcloudService():

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.cred = credential.Credential(self.key, self.secret) 
        self.httpProfile = HttpProfile()
        self.httpProfile.endpoint = "cvm.tencentcloudapi.com"
        self.clientProfile = ClientProfile()
        self.clientProfile.httpProfile = self.httpProfile
    
    def get_all_region(self):
        try: 
            client = cvm_client.CvmClient(self.cred, "", self.clientProfile) 

            req = models.DescribeRegionsRequest()
            params = '{}'
            req.from_json_string(params)

            resp = client.DescribeRegions(req) 
            return resp.to_json_string()
        except TencentCloudSDKException as err: 
            print(err)

    def get_allhost(self, region="ap-beijing"):
        self.region = region
        try: 
            client = cvm_client.CvmClient(self.cred, self.region, self.clientProfile) 

            req = models.DescribeHostsRequest()
            params = '{}'
            req.from_json_string(params)

            resp = client.DescribeHosts(req) 
            return resp.to_json_string()

        except TencentCloudSDKException as err: 
            print(err) 

class AliyunService():

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.client = AcsClient(
                self.key,
                self.secret,
                'cn-beijing',
        )
        self.request = CommonRequest()
        self.request.set_accept_format('json')
        self.request.set_domain('ecs.aliyuncs.com')
        self.request.set_method('POST')
        self.request.set_version('2014-05-26')

    def get_all_region(self):
        try: 
            self.request.set_action_name('DescribeRegions')

            return self.client.do_action(self.request)
            # python2:  print(response) 
            # print(str(response, encoding = 'utf-8'))
        except: 
            pass
    
    def get_allhost(self, region="cn-beijing"):
        self.region = region
        try:
            self.request.set_action_name('DescribeInstances')
            self.request.add_query_param('RegionId', self.region)

            return self.client.do_action(self.request)
        except:
            pass
