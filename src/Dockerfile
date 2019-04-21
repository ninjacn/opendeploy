FROM python:3.7.2-stretch

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update

RUN apt-get install -y libsasl2-dev libldap2-dev rsync vim git dos2unix subversion
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y locales

RUN pip3 install pipenv
RUN rm -rf /var/lib/apt/lists/*

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

RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8  
ENV LANGUAGE en_US:en  
ENV LC_ALL en_US.UTF-8
