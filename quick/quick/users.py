#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.template.loader import get_template
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core import serializers
import simplejson
import hashlib
import uuid
from datetime import datetime
import install
import assets
from quick.models import *
from error_page import error_page
import oauth
from login import login
'''
import xmlrpclib
import cobbler.utils as utils
'''
#========================================================================
@csrf_protect
def user_edit(request,what,obj_name=None, editmode='edit'):
    """
    Let's the user know what to expect for event updates.
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/user/%s/list"%what, expired=True)

    have_groups=[]
    have_rights=[]
    users=[]
    groups = Groups.objects.all()
    rights = Rights.objects.all()
    if editmode == 'edit':
        editable = False
        if what == 'user':
            if obj_name:
                item = Users.objects.get(username=obj_name)
                if item:
                    user_groups = User_Group.objects.filter(user_id=item.id)
                    if user_groups:
                        for user_group in user_groups:
                            group_obj = Groups.objects.get(id=user_group.group_id)
                            have_groups.append(group_obj.name)
                    user_rights = User_Right.objects.filter(user_id=item.id)
                    if user_rights:
                        for user_right in user_rights:
                            right_obj = Rights.objects.get(id=user_right.right_id)
                            have_rights.append(right_obj.name)
        elif what == 'role':
            if obj_name:
                item = Groups.objects.get(name=obj_name)
                if item:
                    group_rights = Group_Right.objects.filter(group_id=item.id)
                    if group_rights:
                        for group_right in group_rights:
                            right_obj = Rights.objects.get(id=group_right.right_id)
                            have_rights.append(right_obj.name)
        elif what == 'right':
            if obj_name:
                item = Rights.objects.get(name=obj_name)
        else:
            item = ''
    else:
        editable = True
        item     = ''
    t = get_template("user_edit.tmpl")
    html = t.render(RequestContext(request,{
        'what'            : "user/%s"%what,
        'name'            : obj_name,
        'editmode'        : editmode,
        'editable'        : editable,
        'item'            : item,
        'groups'          : groups,
        'rights'          : rights,
        'have_groups'     : have_groups,
        'have_rights'     : have_rights,
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)
#========================================================================
@require_POST
@csrf_protect
def user_save(request,what):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/user/%s/list"%what, expired=True)
    editmode = request.POST.get('editmode', 'edit')
    group_name_list = request.POST.getlist('to_group', "")
    right_name_list = request.POST.getlist('to_right', "")
    if what == 'user':
        username = request.POST.get('username', "")
        if username == "":
            return error_page(request,"用户名不能为空")
        name = request.POST.get('name', "")
        telephone = request.POST.get('telephone', "")
        employee_id = request.POST.get('employee_id', "")
        pwd = request.POST.get('pwd', "")
        email = request.POST.get('email', "")
        is_active = request.POST.get('is_active', "")
        is_superuser = request.POST.get('is_superuser', "")
        if is_active:
            is_active = 'yes'
        else:
            is_active = 'no'
        if is_superuser:
            is_superuser='yes'
        else:
            is_superuser='no'
        if editmode != 'edit':
            password_md5 = hashlib.md5(pwd.encode(encoding='UTF-8')).hexdigest()
            try:
                user=Users(employee_id=employee_id,username=username,password=password_md5,email=email,name=name,telephone=telephone,sex='f',photo='none',token=str(uuid.uuid4()).replace('-',''),token_expire_time=str(uuid.uuid4()).replace('-',''),reset_token=str(uuid.uuid4()).replace('-',''),reset_token_expire_time=str(uuid.uuid4()).replace('-',''),is_superuser=is_superuser,is_active=is_active,registry_time=datetime.now())
                user.save()
                user = Users.objects.get(username=username)
                user_profile = User_Profile(user_id=user.id,username=user.username)
                user_profile.save()
                if user and group_name_list:
                    for group_name in group_name_list:
                        role = Groups.objects.get(name=group_name)
                        user_role= User_Group(user_id=user.id,group_id=role.id)
                        user_role.save()
                if user and right_name_list:
                    for right_name in right_name_list:
                        right = Rights.objects.get(name=right_name)
                        user_right= User_Right(user_id=user.id,right_id=right.id)
                        user_right.save()
            except Exception,e:
                return error_page(request,str(e))
        else:
            user = Users.objects.get(username=username)
            if user.password == pwd:
                password = pwd
            else:
                password = hashlib.md5(pwd.encode(encoding='UTF-8')).hexdigest()
            user.name = name
            user.telephone = telephone
            user.is_active = is_active
            user.is_superuser = is_superuser
            user.password = password
            user.email = email
            user.save()
            User_Group.objects.filter(user_id=user.id).delete()
            User_Right.objects.filter(user_id=user.id).delete()
            if user and group_name_list:
                for group_name in group_name_list:
                    role = Groups.objects.get(name=group_name)
                    user_group = User_Group(user_id=user.id,group_id=role.id)
                    user_group.save()
            if user and right_name_list:
                for right_name in right_name_list:
                    right = Rights.objects.get(name=right_name)
                    user_right = User_Right(user_id=user.id,right_id=right.id)
                    user_right.save()
    elif what == 'role':
        name = request.POST.get('name', "")
        if name == "":
            return error_page(request,"角色名称不能为空")
        desc = request.POST.get('desc', "")
        if editmode != 'edit':
            role = Groups(name=name,desc=desc)
            role.save()
            if role and right_name_list:
                for right_name in right_name_list:
                    right = Rights.objects.get(name=right_name)
                    group_right= Group_Right(group_id=role.id,right_id=right.id)
                    group_right.save()
        else:
            role = Groups.objects.get(name=name)
            role.desc = desc
            role.save()
            if role and right_name_list:
                for right_name in right_name_list:
                    right = Rights.objects.get(name=right_name)
                    is_exist = Group_Right.objects.filter(group_id=role.id,right_id=right.id)
                    if is_exist:
                        continue
                    else:
                        group_right = Group_Right(group_id=role.id,right_id=right.id)
                        group_right.save()
    elif what == 'right':
        name = request.POST.get('name', "")
        if name == "":
            return error_page(request,"权限名称不能为空")
        menu1_title = request.POST.get('menu1_title', "")
        menu1_icon  = request.POST.get('menu1_icon', "")
        menu2_title = request.POST.get('menu2_title', "")
        menu2_url   = request.POST.get('menu2_url', "")
        desc = request.POST.get('desc', "")
        if editmode != 'edit':
            right = Rights(name=name,menu1_title=menu1_title,menu1_icon=menu1_icon,
                           menu2_title=menu2_title,menu2_url=menu2_url,desc=desc)
            right.save()
        else:
            right = Rights.objects.get(name=name)
            right.menu1_title = menu1_title
            right.menu1_icon  = menu1_icon
            right.menu2_title = menu2_title
            right.menu2_url   = menu2_url
            right.desc        = desc
            right.save()
    else:
        pass
    return HttpResponseRedirect('/quick/user/%s/list'%what)
#========================================================================
def user_list(request,what,page=None):
    """
    Let's the user know what to expect for event updates.
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/user/%s/list"%what, expired=True)
    if page == None:
        page = int(request.session.get("%s_page"%what, 1))
    limit = int(request.session.get("%s_limit"%what , 20))
    sort_field = sort_field_old = request.session.get("%s_sort_field"%what, "id")
    if sort_field.startswith("!"):
        sort_field=sort_field.replace("!","-")
    filters = simplejson.loads(request.session.get("%s_filters"%what, "{}"))

    num_items  = request.session.get("%s_num_items"%what,None)
    if what == 'user':
        """
        测试用
        url_cobbler_api = utils.local_get_cobbler_api_url()
        remote = xmlrpclib.Server(url_cobbler_api, allow_none=True)
        settings = remote.get_settings()
        return HttpResponse(simplejson.dumps(settings,ensure_ascii=False),content_type="application/json,charset=utf-8")
        """
        batchactions = [["删除","delete","delete"],
                        ["禁用","account","disable"],
                        ["启用","account","enable"]
                       ]
        fields = [f for f in Users._meta.fields]
        if not num_items:
            items = Users.objects.filter(**filters).order_by(sort_field)
            json_data = serializers.serialize("json", items)
            request.session["user_json_data"] = json_data
            num_items = request.session["app_num_items"] = len(items)
            items = items[:limit]
        else:
            offset = (page -1 )*limit
            end = page*limit
            items = Users.objects.filter(**filters).order_by(sort_field)[offset:end]
    elif what == 'role':
        batchactions = [["删除","delete","delete"],]
        fields = [f for f in Groups._meta.fields]
        if not num_items:
            items = Groups.objects.filter(**filters).order_by(sort_field)
            json_data = serializers.serialize("json",items)
            request.session["role_json_data"] = json_data
            num_items = request.session["hardware_num_items"] = len(items)
            items = items[:limit]
        else:
            offset = (page -1 )*limit
            end = page*limit
            items = Groups.objects.filter(**filters).order_by(sort_field)[offset:end]
    elif what == 'right':
        batchactions = [["删除","delete","delete"],]
        fields = [f for f in Rights._meta.fields]
        if not num_items:
            items = Rights.objects.filter(**filters).order_by(sort_field)
            json_data = serializers.serialize("json", items)
            request.session["right_json_data"] = json_data
            num_items = request.session["right_num_items"] = len(items)
            items = items[:limit]
        else:
            offset = (page -1 )*limit
            end = page*limit
            items = Rights.objects.filter(**filters).order_by(sort_field)[offset:end]
    else:
        return HttpResponse("not found!")
    columns=[]
    exclude = ['password','id','employee_id','photo','token','token_expire_time','reset_token','reset_token_expire_time','sex']
    for field in fields:
        if field.name in exclude:
            continue
        columns.append([field.name,field.verbose_name,'on'])
    t = get_template("user_list.tmpl")
    html = t.render(RequestContext(request,{
        'what'           : "user/%s"%what,
        'columns'        : assets.__format_columns(columns,sort_field_old),
        'items'          : assets.__format_items(items,columns),
        'pageinfo'       : assets.__paginate(num_items,page=page,items_per_page=limit),
        'filters'        : filters,
        'limit'          : limit,
        'batchactions'   : batchactions,
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

# ======================================================================

@require_POST
@csrf_protect
def user_domulti(request,what,multi_mode=None, multi_arg=None):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/user/%s/list"%what, expired=True)

    names = request.POST.get('names', '').strip().split()
    if names == "":
        return error_page(request, "未选中任何对象")
    if what == "user":
        if multi_mode == "delete" and multi_arg == 'delete':
            for username in names:
                user = Users.objects.get(username=username)
                User_Right.objects.filter(user_id=user.id).delete()
                User_Group.objects.filter(user_id=user.id).delete()
                user.delete()
        elif multi_mode == "account" and multi_arg == 'disable':
            for username in names:
                user = Users.objects.get(username=username)
                user.is_active='no'
                user.save()
        elif multi_mode == "account" and multi_arg == 'enable':
            for username in names:
                user = Users.objects.get(username=username)
                user.is_active='yes'
                user.save()
        elif multi_mode == "account" and multi_arg == 'offline':
            for username in names:
                '''
                user = Users.objects.get(username=username)
                user.is_online='offline'
                user.save()
                '''
        else:
            return error_page(request,"未知操作")
    elif what == "role":
        if multi_mode == "delete" and multi_arg == 'delete':
            for name in names:
                group = Groups.objects.get(name=name)
                Group_Right.objects.filter(group_id=group.id).delete()
                User_Group.objects.filter(group_id=group.id).delete()
                group.delete()
        else:
            return error_page(request,"未知操作")
    elif what == 'right':
        if multi_mode == "delete" and multi_arg == 'delete':
            for name in names:
                right = Rights.objects.get(name=name)
                Group_Right.objects.filter(right_id=right.id).delete()
                User_Right.objects.filter(right_id=right.id).delete()
                right.delete()
        else:
            return error_page(request,"未知操作")
    return HttpResponseRedirect("/quick/user/%s/list"%what)
# ======================================================================
def user_manual(request,what,action=None,name=None):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/user/%s/list"%what, expired=True)
    if what == 'user':
        if action == "delete" and name:
            user = Users.objects.get(username=name)
            User_Right.objects.filter(user_id=user.id).delete()
            User_Group.objects.filter(user_id=user.id).delete()
            user.delete()
        elif action == "offline" and name:
            '''
            user = Users.objects.get(username=name)
            user.is_online='offline'
            user.save()
            '''
        else:
            return error_page(request,"未知操作")
    elif what == 'role':
        if action == "delete" and name:
            role = Groups.objects.get(name=name)
            role.delete()
    elif what == 'right':
        if action == "delete" and name:
            right = Rights.objects.get(name=name)
            right.delete()
    else:
        pass
    return HttpResponseRedirect("/quick/user/%s/list"%what)
# ======================================================================
@require_POST
@csrf_protect
def modify_list(request, what, pref, value=None):
    """
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/user/%s/list" %what, expired=True)

    if pref == "sort":

        old_sort = request.session.get("%s_sort_field" % what,"name")
        if old_sort.startswith("!"):
            old_sort = old_sort[1:]
            old_revsort = True
        else:
            old_revsort = False

        if old_sort == value and not old_revsort:
            value = "!" + value
        request.session["%s_sort_field" % what] = value
        request.session["%s_page" % what] = 1

    elif pref == "limit":
        # 每页显示的条目数
        request.session["%s_limit" % what] = int(value)
        request.session["%s_page" % what] = 1

    elif pref == "page":
        # 当前页面数字
        request.session["%s_page" % what] = int(value)

    elif pref in ("addfilter","removefilter"):
        # filters limit what we show in the lists
        # they are stored in json format for marshalling
        filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))
        if pref == "addfilter":
            (field_name, field_value) = value.split(":", 1)
            # add this filter
            filters[field_name] = field_value
        else:
            # remove this filter, if it exists
            if filters.has_key(value):
                del filters[value]
        # save session variable
        request.session["%s_filters" % what] = simplejson.dumps(filters)
        # since we changed what is viewed, reset the page
        request.session["%s_page" % what] = 1

    else:
        return error_page(request, "无效请求")

    # redirect to the list page
    return HttpResponseRedirect("/quick/user/%s/list" % what)
#==================================================================================

def changepwd(request):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/user/changepwd", expired=True)
    t = get_template("personal.tmpl")
    html = t.render(RequestContext(request,{
        'what' : "changepwd",
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

def myinfo(request):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/user/myinfo", expired=True)
    meta = simplejson.loads(request.session['quick_meta'])
    item = Users.objects.filter(username=meta['username'])
    fields = [f for f in Users._meta.fields]
    columns=[]
    exclude = ['id','last_login','is_superuser','is_active','registry_time','password',
                         'photo','token','token_expire_time','reset_token','reset_token_expire_time']
    for field in fields:
        if field.name in exclude:
            continue
        columns.append([field.name,field.verbose_name])
    newitem = []
    for name,verbose_name in columns:
        newitem.append([name,getattr(item[0], name),'',verbose_name])
    t = get_template("personal.tmpl")
    html = t.render(RequestContext(request,{
        'what'           : "myinfo",
        'items'          : newitem,
        'meta'           : meta
    }))
    return HttpResponse(html)

@require_POST
@csrf_protect
def my_save(request):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/user/myinfo", expired=True)
    meta = simplejson.loads(request.session['quick_meta'])
    username = meta['username']
    if request.POST.get('newpwd','') and request.POST.get('newpwd2',''):
        user = Users.objects.get(username = username)
        newpwd = request.POST.get('newpwd','')
        newpwd2 = request.POST.get('newpwd2','')
        if newpwd == newpwd2:
            user.password = password_md5 = hashlib.md5(newpwd.encode(encoding='UTF-8')).hexdigest()
            user.save()
            return HttpResponseRedirect('/quick/user/changepwd')
        else:
            return error_page(request,'两次输入密码不一致！')
    else:
        try:
            user = Users.objects.get(username=username)
            fields = [f for f in Users._meta.fields]
            kw = {}
            exclude = ['id','last_login','is_superuser','is_active','registry_time','password',
                         'photo','token','token_expire_time','reset_token','reset_token_expire_time']
            for field in fields:
                if field.name in exclude:
                    continue
                kw[field.name] = request.POST.get(field.name, "")
            for k,v in kw.items():
                setattr(user, k , v)
            user.save()
        except Exception,e:
            pass
        return HttpResponseRedirect('/quick/user/myinfo')
#==================================================================================

def logit(request,what,page=None):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/%s"%what, expired=True)
    if page == None:
        page = int(request.session.get("%s_page"%what, 1))
    limit = int(request.session.get("%s_limit"%what ,10))
    sort_field = sort_field_old = request.session.get("%s_sort_field"%what, "id")
    batchactions = [["删除","delete","delete"]]
    if sort_field.startswith("!"):
        sort_field=sort_field.replace("!","-")
    filters = simplejson.loads(request.session.get("%s_filters"%what, "{}"))
    num_items  = request.session.get("%s_num_items"%what,None)
    if what == 'manual':
        fields = [f for f in Manual_Log._meta.fields]
        if not num_items:
            items = Manual_Log.objects.filter(**filters).order_by(sort_field)
            json_data = serializers.serialize("json", items)
            request.session["%s_json_data"%what] = json_data
            num_items = request.session["%s_num_items"%what] = len(items)
            items = items[:limit]
        else:
            offset = (page -1 )*limit
            end = page*limit
            items = Manual_Log.objects.filter(**filters).order_by(sort_field)[offset:end]
    elif what == 'login':
        fields = [f for f in Login_Log._meta.fields]
        if not num_items:
            items = Login_Log.objects.filter(**filters).order_by(sort_field)
            json_data = serializers.serialize("json", items)
            request.session["%s_json_data"%what] = json_data
            num_items = request.session["%s_num_items"%what] = len(items)
            items = items[:limit]
        else:
            offset = (page -1 )*limit
            end = page*limit
            items = Login_Log.objects.filter(**filters).order_by(sort_field)[offset:end]
    elif what == 'asset':
        fields = [f for f in Asset_Log._meta.fields]
        if not num_items:
            items = Asset_Log.objects.filter(**filters).order_by(sort_field)
            json_data = serializers.serialize("json", items)
            request.session["%s_json_data"%what] = json_data
            num_items = request.session["%s_num_items"%what] = len(items)
            items = items[:limit]
        else:
            offset = (page -1 )*limit
            end = page*limit
            items = Asset_Log.objects.filter(**filters).order_by(sort_field)[offset:end]
    else:
        pass
    columns=[]
    exclude = []
    for field in fields:
        if field.name in exclude:
            continue
        columns.append([field.name,field.verbose_name,'on'])
    t = get_template("logit.tmpl")
    html = t.render(RequestContext(request,{
        'what'           : 'log/%s'%what,
        'columns'        : assets.__format_columns(columns,sort_field_old),
        'items'          : assets.__format_items(items,columns),
        'pageinfo'       : assets.__paginate(num_items,page=page,items_per_page=limit),
        'filters'        : filters,
        'limit'          : limit,
        'batchactions'   : batchactions,
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)



