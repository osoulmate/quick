#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.template.loader import get_template
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import simplejson
from datetime import datetime
import views
import tasks
from quick.models import Users,Groups,Rights,User_Group,Group_Right,User_Right

#========================================================================
@csrf_protect
def user_edit(request,user_name=None, editmode='edit'):
    """
    Let's the user know what to expect for event updates.
    """
    if editmode == 'edit':
         editable = False
    else:
         editable = True
    have_groups=[]
    have_rights=[]
    user_result=[]
    if user_name:
        user_result = Users.objects.get(username=user_name)
        if user_result:
            user_groups = User_Group.objects.filter(user_id=user_result.id)
            if user_groups:
                for user_group in user_groups:
                    group_obj = Groups.objects.get(id=user_group.group_id)
                    have_groups.append(group_obj.name)
            user_rights = User_Right.objects.filter(user_id=user_result.id)
            if user_rights:
                for user_right in user_rights:
                    right_obj = Rights.objects.get(id=user_right.right_id)
                    have_rights.append(right_obj.codename)
    group_result_all = Groups.objects.all()
    right_reslut_all = Rights.objects.all()
    t = get_template("user_edit.tmpl")
    html = t.render(RequestContext(request,{
        'name'              : user_name,
        'editmode'        : editmode,
        'editable'        : editable,
        'user_result'     : user_result,
        'groups'          : group_result_all,
        'rights'          : right_reslut_all,
        'have_groups'     : have_groups,
        'have_rights'     : have_rights,
        'username'        : views.username,
        'menu'  :views.menu
    }))
    return HttpResponse(html)
#========================================================================
def user_check(username,password):
    result = Users.objects.filter(username=username,password=password)
    if result:
        return True
    else:
        return False
#========================================================================
@require_POST
@csrf_protect
def user_save(request):
    if not views.test_user_authenticated(request): return views.login(request, next="/quick/task/save/%s" % task_name, expired=True)
    editmode = request.POST.get('editmode', 'edit')
    username = request.POST.get('username', "")
    if username == "":
        return views.error_page(request,"用户名不能为空")
    first_name = request.POST.get('first_name', "")
    last_name = request.POST.get('last_name', "")
    is_active = request.POST.get('is_active', "")
    is_superuser = request.POST.get('is_superuser', "")
    if is_active:
        is_active = 'enable'
    else:
        is_active = 'disable'
    if is_superuser:
        is_superuser='yes'
    else:
        is_superuser='no'
    pwd = request.POST.get('pwd', "")
    email = request.POST.get('email', "")

    group_name_list = request.POST.getlist('to_group', "")
    right_codename_list = request.POST.getlist('to_right', "")
    if editmode != 'edit':
        user_add=Users(username=username,password=pwd,email=email,first_name=first_name,
            last_name=last_name,last_login=datetime.now(),is_superuser=is_superuser,is_active=is_active,is_online='offline')
        user_add.save()
        user_result = Users.objects.get(username=username)
        if user_result and group_name_list:
            for group in group_name_list:
                group_result = Groups.objects.get(name=group)
                user_group_add= User_Group(user_id=user_result.id,group_id=group_result.id)
                user_group_add.save()
        if user_result and right_codename_list:
            for right in right_codename_list:
                right_reslut = Rights.objects.get(codename=right)
                user_right_add= User_Right(user_id=user_result.id,right_id=right_reslut.id)
                user_right_add.save()
    else:
        update_user = Users.objects.get(username=username)
        update_user.first_name = first_name
        update_user.last_name = last_name
        update_user.is_active = is_active
        update_user.is_superuser = is_superuser
        update_user.password = pwd
        update_user.email = email
        update_user.save()
        User_Group.objects.filter(user_id=update_user.id).delete()
        User_Right.objects.filter(user_id=update_user.id).delete()
        if update_user and group_name_list:
            for group in group_name_list:
                group_result = Groups.objects.get(name=group)
                insert_user_group = User_Group(user_id=update_user.id,group_id=group_result.id)
                insert_user_group.save()
        if update_user and right_codename_list:
            for right in right_codename_list:
                right_reslut = Rights.objects.get(codename=right)
                insert_user_right = User_Right(user_id=update_user.id,right_id=right_reslut.id)
                insert_user_right.save()

    return HttpResponseRedirect('/quick/user/list')
#========================================================================
def user_list(request,page=None):
    """
    Let's the user know what to expect for event updates.
    """
    if not views.test_user_authenticated(request): return views.login(request, next="/quick/user/list", expired=True)
    if page == None:
        page = int(request.session.get("user_page", 1))
    limit = int(request.session.get("user_limit" , 20))
    sort_field = sort_field1 = request.session.get("user_sort_field", "username")
    if sort_field.startswith("!"):
        sort_field=sort_field.replace("!","-")
    filters = simplejson.loads(request.session.get("user_filters", "{}"))

    columns = [ "username","email","last_login","registry_time","is_active","is_online","is_superuser"]
    batchactions = [["删除","delete","delete"],["禁用","account","disable"],["启用","account","enable"],]
    result = Users.objects.filter(**filters).order_by(sort_field)
    t = "user_list.tmpl"

    (items,pageinfo) = tasks.__paginate(result,page=page,items_per_page=limit)

    t = get_template(t)
    html = t.render(RequestContext(request,{
        'what'     : 'user',
        'columns'        : tasks.__format_columns(columns,sort_field1),
        'items'          : tasks.__format_items(items,columns),
        'pageinfo'       : pageinfo,
        'filters'        : filters,
        'limit'          : limit,
        'username'        : views.username,
        'batchactions'    : batchactions,
        'menu'  :views.menu
    }))
    return HttpResponse(html)

# ======================================================================

@require_POST
@csrf_protect
def user_domulti(request,multi_mode=None, multi_arg=None):
    if not views.test_user_authenticated(request): return views.login(request, next="/quick/user/list", expired=True)

    names = request.POST.get('names', '').strip().split()
    if names == "":
        return views.error_page(request, "未选中任何对象")

    if multi_mode == "delete" and multi_arg == 'delete':
        for username in names:
            user = Users.objects.get(username=username)
            User_Right.objects.filter(user_id=user.id).delete()
            User_Group.objects.filter(user_id=user.id).delete()
            user.delete()
    elif multi_mode == "account" and multi_arg == 'disable':
        for username in names:
            user = Users.objects.get(username=username)
            user.is_active='disable'
            user.save()
    elif multi_mode == "account" and multi_arg == 'enable':
        for username in names:
            user = Users.objects.get(username=username)
            user.is_active='enable'
            user.save()
    elif multi_mode == "account" and multi_arg == 'offline':
        for username in names:
            user = Users.objects.get(username=username)
            user.is_online='offline'
            user.save()
    else:
        return views.error_page(request,"未知操作")
    return HttpResponseRedirect("/quick/user/list")
# ======================================================================
def user_single(request,action=None, name=None):
    if not views.test_user_authenticated(request): return views.login(request, next="/quick/user/list", expired=True)
    if action == "delete" and name:
            user = Users.objects.get(username=name)
            User_Right.objects.filter(user_id=user.id).delete()
            User_Group.objects.filter(user_id=user.id).delete()
            user.delete()
    elif action == "offline" and name:
            user = Users.objects.get(username=name)
            user.is_online='offline'
            user.save()
    else:
        return views.error_page(request,"未知操作")
    return HttpResponseRedirect("/quick/user/list")


