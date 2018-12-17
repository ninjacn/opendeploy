# -*- coding: utf-8 -*-
# Author: Pengming Yao<x@ninjacn.com>
# Date created: 2018-12-16

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User

from admin.forms import UserEditForm, UserAddForm

@user_passes_test(lambda u: u.is_superuser)
def all_users(request):
    all_users = User.objects.all()
    return render(request, 'admin/accounts/all_users.html', {
        'all_users': all_users,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def user_add(request):
    if request.method== 'POST':
        f = UserAddForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                user = User()
                user.username = cleaned_data.get('username')
                user.set_password(cleaned_data.get('password'))
                user.email = cleaned_data.get('email')
                user.first_name = cleaned_data.get('first_name')
                user.is_superuser = cleaned_data.get('is_superuser')
                user.is_active = cleaned_data.get('is_active')
                user.is_staff = 0
                user.save()
                messages.info(request, '操作成功')
            except:
                messages.error(request, '操作失败')
            finally:
                return redirect('admin:accounts.all_users')
        else:
            print(f.errors)
    else:
        f = UserAddForm()
    return render(request, 'admin/accounts/user_add.html', {
        "form": f,
    })


@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def user_edit(request, uid):
    user = User.objects.get(pk=uid)
    if request.method== 'POST':
        f = UserEditForm(request.POST, user=user)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                user.username = cleaned_data.get('username')
                user.email = cleaned_data.get('email')
                user.first_name = cleaned_data.get('first_name')
                user.is_superuser = cleaned_data.get('is_superuser')
                user.is_active = cleaned_data.get('is_active')
                user.is_staff = 0
                user.save()
                messages.info(request, '操作成功')
            except:
                messages.error(request, '操作失败')
            finally:
                return redirect('admin:accounts.all_users')
        else:
            print(f.errors)
    else:
        f = UserEditForm()
    return render(request, 'admin/accounts/user_edit.html', {
        "form": f,
        "user": user,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def user_del(request, uid):
    try:
        user = User.objects.get(id=uid)
        user.delete()
        messages.info(request, '删除成功')
    except:
        messages.error(request, '用户不存在')
    return redirect('admin:accounts.all_users')
