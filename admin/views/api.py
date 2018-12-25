# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-24
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from uuid import uuid4

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test

from api.models import Token
from admin.forms import ApiTokenForm

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def token(request):
    all_token = Token.objects.all()
    return render(request, 'admin/api/token.html', {
        "all_token": all_token,
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def token_add(request):
    if request.method== 'POST':
        f = ApiTokenForm(request.POST)
        if f.is_valid():
            cleaned_data = f.cleaned_data
            try:
                token = Token()
                token.title = cleaned_data['title']
                token.token = cleaned_data['token']
                token.save()
                messages.info(request, '添加成功')
            except:
                messages.error(request, '添加失败')
            finally:
                return redirect('admin:api.token')
    else:
        f = ApiTokenForm()
    return render(request, 'admin/api/add_token.html', {
        "form": f,
        "auto_generate_token": uuid4(),
    })

@user_passes_test(lambda u: u.is_superuser)
@transaction.atomic
def token_del(request, id):
    try:
        token = Token.objects.get(id=id)
        token.delete()
        messages.info(request, '删除成功')
    except:
        messages.error(request, '删除失败')
    return redirect('admin:api.token')

