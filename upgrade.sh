#!/bin/bash
# 升级服务

#git clean -df &&
#    git reset --hard HEAD &&
    git pull origin master &&
    docker-compose exec web python manage.py migrate --noinput
