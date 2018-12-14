from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout
from django.db import transaction

from opendeploy import settings
from .forms import RegisterForm, LoginForm

# Create your views here.

@transaction.atomic
def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=raw_password)
            if user is not None:
                auth_login(request, user)
                return redirect('/')
            else:
                form.add_error('username', '认证失败，邮箱或密码错误!')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            username = email.split('@')[0]
            raw_password = form.cleaned_data.get('password1')
            user = User()
            user.username = username
            user.email = email
            user.first_name = form.cleaned_data.get('first_name')
            user.set_password(raw_password)
            user.save()

            user = authenticate(username=username, password=raw_password)
            auth_login(request, user)
            return redirect('/')
    else:
        form = RegisterForm()
    # return TemplateResponse(request, 'accounts/register.html', {'form': form})
    return render(request, 'accounts/register.html', {'form': form})
