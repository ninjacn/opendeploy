# -*- coding: utf-8 -*-
#
# (c) Pengming Yao<x@ninjacn.com>
#
# 2018-12-16
#
# For the full copyright and license information, please view the LICENSE
# file that was distributed with this source code.

from django.shortcuts import render, redirect
from django.http import HttpResponse, Http404
from django.template.response import TemplateResponse
from django.db import transaction
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from opendeploy import settings
from admin.forms import UserEditForm, UserAddForm
from accounts.models import UserDetail

@user_passes_test(lambda u: u.is_superuser)
def all_users(request):
    q = request.GET.get('q')
    if q:
        all_users = User.objects.filter(Q(username__contains=q) | Q(last_name__contains=q) | Q(first_name__contains=q) | Q(email__contains=q))
    else:
        all_users = User.objects.all().order_by('-is_active')
    paginator = Paginator(all_users, settings.PAGE_SIZE)
    page = request.GET.get('page')
    if not page:
        page = 1
    try:
        all_users_p = paginator.page(page)
    except PageNotAnInteger:
        all_users_p = paginator.page(1)
    except EmptyPage:
        all_users_p = paginator.page(paginator.num_pages)

    def rebuild_users(user):
        try:
            user_detail = UserDetail.objects.get(username=user)
            user.user_type = user_detail.get_type_display
        except:
            user.user_type = dict(UserDetail.TYPE_CHOICES)[UserDetail.TYPE_LOCAL]
        return user
    all_users = map(rebuild_users, all_users_p)
    get_copy = request.GET.copy()
    parameters = get_copy.pop('page', True) and get_copy.urlencode()

    return render(request, 'admin/accounts/all_users.html', {
        'all_users': all_users,
        'all_users_p': all_users_p,
        'parameters': parameters,
        'q': q,
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
    try:
        user = User.objects.get(pk=uid)
    except:
        raise Http404('用户不存在')
    try:
        user_detail = UserDetail.objects.get(username=user)
        user_type = user_detail.type
        ldap_dn = user_detail.ldap_dn
    except:
        user_type = UserDetail.TYPE_LOCAL
        ldap_dn = ''

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

                try:
                    user_detail = UserDetail.objects.get(username=user)
                    user_detail.type = request.POST.get('type')
                    user_detail.ldap_dn = request.POST.get('ldap_dn')
                    user_detail.save()
                except:
                    user_detail = UserDetail()
                    user_detail.username = user
                    user_detail.type = request.POST.get('type')
                    user_detail.save()
                    pass
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
        "user_type": user_type,
        "ldap_dn": ldap_dn,
        "user": user,
        "type_choices": UserDetail.TYPE_CHOICES,
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
