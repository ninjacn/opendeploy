# -*- coding: utf-8 -*-
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException 
from tencentcloud.cvm.v20170312 import cvm_client, models 

from setting.services import SettingService


class Qcloud():
    
    def get_allhost(self, region="ap-beijing"):
        try: 
            settingService = SettingService()
            auth_info = settingService.get_public_cloud_info()
            if auth_info is None:
                return None

            cred = credential.Credential(auth_info.qcloud_secret_id, auth_info.qcloud_secret_key) 
            httpProfile = HttpProfile()
            httpProfile.endpoint = "cvm.tencentcloudapi.com"

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = cvm_client.CvmClient(cred, region, clientProfile) 

            req = models.DescribeHostsRequest()
            params = '{}'
            req.from_json_string(params)

            resp = client.DescribeHosts(req) 
            print(resp.to_json_string()) 

        except TencentCloudSDKException as err: 
            print(err) 
