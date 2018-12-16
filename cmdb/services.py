# -*- coding: utf-8 -*-
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException 
from tencentcloud.cvm.v20170312 import cvm_client, models 

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException
from aliyunsdkecs.request.v20140526 import DescribeInstancesRequest
from aliyunsdkecs.request.v20140526 import StopInstanceRequest

from setting.services import SettingService


class Qcloud():

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
    
    def get_all_region(self):
        pass

    def get_allhost(self, region="ap-beijing"):
        self.region = region
        try: 
            cred = credential.Credential(self.key, self.secret) 
            httpProfile = HttpProfile()
            httpProfile.endpoint = "cvm.tencentcloudapi.com"

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = cvm_client.CvmClient(cred, self.region, clientProfile) 

            req = models.DescribeHostsRequest()
            params = '{}'
            req.from_json_string(params)

            resp = client.DescribeHosts(req) 
            print(resp.to_json_string()) 

        except TencentCloudSDKException as err: 
            print(err) 

class Aliyun():

    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def get_all_region(self):
        pass
    
    def get_allhost(self, region="cn-beijing"):
        self.region = region
        try: 
            client = AcsClient(
                    self.key,
                    self.secret,
                    self.region,
            )
            request = DescribeInstancesRequest.DescribeInstancesRequest()
            request.set_PageSize(10)

            response = client.do_action_with_exception(request)
            print(response)
        except: 
            pass
