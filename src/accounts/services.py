# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-23
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import ldap

from django.contrib.auth.models import User
from accounts.models import UserDetail
from setting.services import SettingService


class LdapService():

    def __init__(self):
        settingService = SettingService()
        self.ldap_info = settingService.get_ldap_info()
        self.ldap_url = ''
        if self.ldap_info:
            self.ldap_url = 'ldap://' + self.ldap_info.host + ':' + self.ldap_info.port
        self.error_msg = None
        self.con = None

    def connect(self):
        con = ldap.initialize(self.ldap_url)
        con.protocol_version = ldap.VERSION3
        try:
            con.simple_bind_s(self.ldap_info.bind_dn, self.ldap_info.password)
            self.con = con
            return True
        except ldap.INVALID_CREDENTIALS as e:
            self.error_msg = '账号密码错误.' 
        except ldap.SERVER_DOWN as e:
            self.error_msg = 'Can\'t contact LDAP server.' 
        except:
            self.error_msg = '未知错误'

    def check_account_valid(self):
        if self.connect():
            return True
        return False

    def login(self, username, password):
        if self.ldap_info.enable:
            if self.connect():
                try:
                    user = User.objects.get(username=username, is_active=1)
                except:
                    self.error_msg = username + '用户不存在'
                    return False
                try:
                    userDetail = UserDetail.objects.get(username=user, type=UserDetail.TYPE_LDAP)
                except:
                    self.error_msg = username + '用户LDAP信息不存在, 请联系管理员'
                    return False

                try:
                    self.con.simple_bind_s(userDetail.ldap_dn, password)
                    return True
                except:
                    return False
        else:
            self.error_msg = 'LDAP账号登录已禁用, 请联系管理员'
        return False


    def get_all_staff(self):
        if self.connect():
            searchFilter = "(objectClass=posixAccount)"
            return self.con.search_st(self.ldap_info.base, ldap.SCOPE_SUBTREE, searchFilter, None)

    def sync_accounts(self):
        all_staff = self.get_all_staff()
        if all_staff:
            for u in all_staff:
                try:
                    dn = u[0]
                    uid = u[1]['uid'][0]
                    mail = u[1]['mail'][0]
                except:
                    continue
                if dn and uid:
                    try:
                        user = User.objects.get(username=uid)

                        try:
                            user_detail = UserDetail.objects.get(username=user)
                            if len(user_detail.ldap_dn) == 0:
                                user_detail.ldap_dn = dn
                                user_detail.save()
                        except:
                            user_detail = UserDetail()
                            user_detail.username = user
                            user_detail.ldap_dn = dn
                            user_detail.type = UserDetail.TYPE_LDAP
                            user_detail.save()
                    except:
                        user = User()
                        user.username = uid
                        user.first_name = uid
                        user.email = mail
                        user.is_active = 1
                        user.is_superuser = 0
                        user.is_staff = 0
                        user.save()

                        user_detail = UserDetail()
                        user_detail.username = user
                        user_detail.ldap_dn = dn
                        user_detail.type = UserDetail.TYPE_LDAP
                        user_detail.save()
