# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-23
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from __future__ import absolute_import, unicode_literals
from opendeploy.celery import app
from celery.decorators import periodic_task
from celery.task.schedules import crontab
from celery.utils.log import get_task_logger

from setting.services import SettingService

logger = get_task_logger(__name__)


@periodic_task(
    run_every=(crontab(minute='*/1')),
    name="sync_ldap_accounts",
    ignore_result=True
)
def sync_ldap_accounts():
    settingService = SettingService()
    ldap_info = settingService.get_ldap_info()
    if ldap_info.enable:
        logger.info("Ldap login is enabled.")
