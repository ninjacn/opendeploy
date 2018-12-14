from django.conf.urls import url

from . import views

app_name='deploy'

urlpatterns = [
    url(r'^$', views.index),
]
