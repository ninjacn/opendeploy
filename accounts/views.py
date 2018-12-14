from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login, logout, authenticate
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from opendeploy import settings
from .forms import RegisterForm, LoginForm, ChangePasswordForm

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
                form.add_error('username', '认证失败，用户名或密码错误!')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@transaction.atomic
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            username = form.cleaned_data.get('username')
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

@login_required
@transaction.atomic
def change_password(request):
    if request.method == 'POST':
        form = ChangePasswordForm(request.POST, user=request.user)
        if form.is_valid():
            username = request.user.username
            raw_password = form.cleaned_data.get('new_password2')
            try:
                user = User.objects.get(username=username)
                user.set_password(raw_password)
                user.save()
                logout(request)
                messages.info(request, '密码修改成功，请重新登录')
                return redirect('login')
            except:
                messages.error(request, '用户身份异常')
        else:
            messages.error(request, '提交密码验证不通过')
    else:
        form = ChangePasswordForm()
    return TemplateResponse(request, 'accounts/change_password.html', {
        'form': form
        })
