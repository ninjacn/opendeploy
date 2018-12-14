from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views
from opendeploy import settings

urlpatterns = [
    url(r'^login$', views.login, name='login'),
    url(r'^profile$', views.login, name='profile'),
    url(r'^register$', views.register, name='register'),
    url(r'^logout$', auth_views.logout, {'next_page': settings.LOGIN_REDIRECT_URL}, name='logout'),
    # url(r'^forget-password$', views.forget_password),
    # url(r'^forget-password-reset$', views.forget_password_reset),
    # url(r'^change-password$', views.change_password),
]
