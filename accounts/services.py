# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-23
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

import ldap

from setting.services import SettingService


class LdapService():

    def __init__(self):
        settingService = SettingService()
        self.ldap_info = settingService.get_ldap_info()
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

    def get_all_staff(self):
        if self.connect():
            searchFilter = "(objectClass=posixAccount)"
            return self.con.search_st(self.ldap_info.base, ldap.SCOPE_SUBTREE, searchFilter, None)
