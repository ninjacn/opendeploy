FROM python:3.7.2-stretch

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update

RUN apt-get install -y libsasl2-dev libldap2-dev

RUN pip3 install pipenv

WORKDIR /app

RUN pip install -U pipenv
RUN pip install pipenv
COPY ./Pipfile /app/Pipfile
RUN pipenv install --system --skip-lock
#COPY . /app
