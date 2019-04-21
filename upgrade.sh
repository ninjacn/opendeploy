#!/bin/bash
# 升级服务

docker pull ninjacn/opendeploy
docker pull ninjacn/opendeploy_nginx

git clean -df &&
    git reset --hard HEAD &&
    git pull origin master &&
    docker-compose down;
    docker-compose pull;
    docker-compose -f docker-compose.yml -f docker-compose-prod.yml up -d && 
    docker-compose exec web python manage.py migrate --noinput

if [ "$?" == 0 ]
then
    docker-compose ps
    printf '\E[32m'; echo "升级完成"; printf '\E[0m'
else
    printf '\E[31m'; echo "升级失败"; printf '\E[0m'
    exit 1
fi
