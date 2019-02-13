FROM python:3.7.2-stretch

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update

RUN apt-get install -y libsasl2-dev libldap2-dev rsync vim git dos2unix

RUN pip3 install pipenv

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN mkdir -p /root/.ssh && \
    chmod 0700 /root/.ssh && \
    ssh-keyscan bitbucket.org > /root/.ssh/known_hosts && \
    ssh-keyscan github.com > /root/.ssh/known_hosts
ADD conf/ssh_key/opendeploy /root/.ssh/id_rsa
ADD conf/ssh_key/opendeploy.pub /root/.ssh/id_rsa.pub
RUN chmod 600 /root/.ssh/id_rsa
