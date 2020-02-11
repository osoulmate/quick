#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.template.loader import get_template
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q
from django.core import serializers
from django.conf import settings
import os
import re
import time
import pyexcel as pe
import simplejson
import oauth
from login import login
from error_page import error_page
import utils
from quick.models import *
#========================================================================
@require_POST
@csrf_protect
def ajax_query(request):
    """
    json_data = request.session.get("%s_json_data"%what,"")
    if json_data:
        return HttpResponse(json_data)
    else:
        return HttpResponse('')
    """
    if request.POST.get('action', ''):
        name  = request.POST.get('name', '')
        value = request.POST.get('view', '')
        what  = request.POST.get('what', '')
        if what == 'asset/app':
            app_temp = App_Temp.objects.get(id=1)
            setattr(app_temp,name,value)
            app_temp.save()
        elif what == 'asset/hardware':
            hd_temp = Hardware_Temp.objects.get(id=1)
            setattr(hd_temp,name,value)
            hd_temp.save()
        elif what == 'asset/ipsn':
            ipsn_temp = Ip_Sn_Temp.objects.get(id=1)
            setattr(ipsn_temp,name,value)
            ipsn_temp.save()
        else:
            pass
        return HttpResponse('ok')
#========================================================================
def asset_list(request,what,page=None):
    """
    资产管理处理逻辑
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    if page == None:
        page = int(request.session.get("%s_page"%what, 1))
    limit = int(request.session.get("%s_limit"%what, 10))
    ippool = request.GET.get('ippool', '')
    iplist = ''
    snlist = ''
    if what == 'app' or what == 'ipsn':
        sort_field =  sort_field_old =request.session.get("%s_sort_field"%what, "ip")
    else:
        sort_field =  sort_field_old =request.session.get("%s_sort_field"%what, "sn")
    if sort_field.startswith("!"):
        sort_field=sort_field.replace("!","-")
    filters = simplejson.loads(request.session.get("%s_filters"%what, "{}"))
    batchactions = [["删除","delete","delete"],]
    if what == 'app':
        fields = [f for f in App._meta.fields]
        f = App_Temp.objects.get(id=1)
        if ippool:
            if ippool.strip()[-1] == ',':
                ippool = ippool[0:-1]
            iplist = ippool.split(",")
        if iplist:
            num_items = len(iplist)
            q = Q()
            q.connector = 'OR'
            for ip in iplist:
                q.children.append(("ip",ip))
            items = App.objects.filter(q).order_by("ip")
        else:
            if not filters:
                app_temp = App_Temp.objects.get(id=1)
                num_items = app_temp.num_items
                num_items = int(num_items)
            else:
                items = App.objects.filter(**filters).order_by(sort_field)
                num_items = len(items)
            offset = (page -1 )*limit
            end = page*limit
            items = App.objects.filter(**filters).order_by(sort_field)[offset:end]
        #json_data = serializers.serialize("json", items)
        #request.session["app_json_data"] = json_data
    elif what == 'hardware':
        fields = [f for f in Hardware._meta.fields]
        f = Hardware_Temp.objects.get(id=1)
        if ippool:
            if ippool.strip()[-1] == ',':
                ippool = ippool[0:-1]
            snlist = ippool.split(',')
        if snlist:
            num_items = len(snlist)
            q = Q()
            q.connector = 'OR'
            for sn in snlist:
                q.children.append(("sn",sn.strip()))
            items = Hardware.objects.filter(q).order_by("sn")
        else:
            if not filters:
                hd_temp = Hardware_Temp.objects.get(id=1)
                num_items = hd_temp.num_items
                num_items = int(num_items)
            else:
                items = Hardware.objects.filter(**filters).order_by(sort_field)
                num_items = len(items)
            offset = (page -1 )*limit
            end = page*limit
            items = Hardware.objects.filter(**filters).order_by(sort_field)[offset:end]
    elif what == 'ipsn':
        fields = [f for f in Ip_Sn._meta.fields]
        f = Ip_Sn_Temp.objects.get(id=1)
        if ippool:
            if ippool.strip()[-1] == ',':
                ippool = ippool[0:-1]
            iplist = ippool.split(",")
        if iplist:
            num_items = len(iplist)
            q = Q()
            q.connector = 'OR'
            for ip in iplist:
                q.children.append(("ip",ip))
            items = Ip_Sn.objects.filter(q).order_by("ip")
        else:
            if not filters:
                ipsn_temp = Ip_Sn_Temp.objects.get(id=1)
                num_items = ipsn_temp.num_items
                num_items = int(num_items)
            else:
                items = Ip_Sn.objects.filter(**filters).order_by(sort_field)
                num_items = len(items)
            offset = (page -1 )*limit
            end = page*limit
            items = Ip_Sn.objects.filter(**filters).order_by(sort_field)[offset:end]
    else:
        return HttpResponse("not found!")
    columns=[]
    for field in fields:
        columns.append([field.name,field.verbose_name,getattr(f,field.name,'on')])
    t = get_template("asset_list.tmpl")

    html = t.render(RequestContext(request,{
        'what'           : "asset/%s"%what,
        'columns'        : __format_columns(columns,sort_field_old),
        'items'          : __format_items(items,columns),
        'pageinfo'       : __paginate(num_items,page=page,items_per_page=limit),
        'filters'        : filters,
        'limit'          : limit,
        'username'       : request.session['username'],
        'batchactions'   : batchactions,
        'menu'           : request.session['%s_menu'%request.session['username']]
    }))
    return HttpResponse(html)

# ======================================================================
@require_POST
@csrf_protect
def asset_save(request,what):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    editmode = request.POST.get('editmode', 'edit')
    iplist = ''
    snlist = ''
    if what == 'app':
        fields = [f for f in App._meta.fields]
        kw = {}
        for field in fields:
            kw[field.name] = request.POST.get(field.name, "")
        if not kw.get('ip',None):
            ippool = request.POST.get("ippool", "")
            if ippool:
                iplist = ippool.split()
                for field in fields:
                    if not kw.get(field.name,None):
                        kw.pop(field.name)
            else:
                return error_page(request,"IP不能为空")
        if editmode != 'edit':
            if iplist:
                for ip in iplist:
                    kw['ip'] = ip
                    app = App.objects.get(ip=kw['ip'])
                    for k,v in kw.items():
                        setattr(app, k , v)
                    app.save()
            else:
                app=App(**kw)
                app.save()
                app_temp = App_Temp.objects.get(id=1)
                app_temp.num_items = str(int(app_temp.num_items) + 1)
                app_temp.save()
        else:
            app = App.objects.get(ip=kw['ip'])
            for k,v in kw.items():
                setattr(app, k , v)
            app.save()
    elif what == 'hardware':
        fields = [f for f in Hardware._meta.fields]
        kw = {}
        for field in fields:
            kw[field.name] = request.POST.get(field.name, "")
        if not kw.get('sn',None):
            snpool = request.POST.get("snpool", "")
            if snpool:
                snlist = snpool.split()
                for field in fields:
                    if not kw.get(field.name,None):
                        kw.pop(field.name)
            else:
                return error_page(request,"序列号不能为空")
        if editmode != 'edit':
            if snlist:
                for sn in snlist:
                    kw['sn'] = sn
                    hd = Hardware.objects.get(sn=kw['sn'])
                    for k,v in kw.items():
                        setattr(hd, k , v)
                    hd.save()
            else:
                hd=Hardware(**kw)
                hd.save()
                hd_temp = Hardware_Temp.objects.get(id=1)
                hd_temp.num_items = str(int(hd_temp.num_items) + 1)
                hd_temp.save()
        else:
            hd = Hardware.objects.get(sn=kw['sn'])
            for k,v in kw.items():
                setattr(hd, k , v)
            hd.save()
    elif what == 'ipsn':
        ip = request.POST.get('ip', "")
        sn = request.POST.get('sn', "")
        if sn == "" or ip == "":
            ippool = request.POST.get("ippool", "")
            snpool = request.POST.get("snpool", "")
            if ippool and snpool:
                iplist = ippool.split()
                snlist = snpool.split()
                if len(iplist) != len(snlist):
                    return error_page(request,"IP和序列号个数不一致")
            else:
                return error_page(request,"IP和序列号不能为空")
        if editmode != 'edit':
            if iplist and snlist:
                num = len(iplist)
                for i in range(num):
                    ipsn = Ip_Sn.objects.filter(ip=iplist[i])
                    if ipsn:
                        ipsn = ipsn[0]
                        ipsn.sn = snlist[i]
                        ipsn.save()
                    else:
                        return error_page(request,"%s不存在"%iplist[i])
            else:
                ipsn=Ip_Sn(sn=sn,ip=ip)
                ipsn.save()
                ipsn_temp = Ip_Sn_Temp.objects.get(id=1)
                ipsn_temp.num_items = str(int(ipsn_temp.num_items) + 1)
                ipsn_temp.save()
        else:
            ipsn = Ip_Sn.objects.get(ip=ip)
            ipsn.sn = sn
            ipsn.save()
    else:
        pass
    return HttpResponseRedirect('/quick/asset/%s/list'%what)
# ======================================================================
@require_POST
@csrf_protect
def asset_import(request,what):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    file = request.FILES['xlsfile']
    if file:
        filepath = os.path.join(settings.MEDIA_ROOT, file.name)
        with open(filepath,'wb') as f:
            for info in file.chunks():
                f.write(info)
    else:
        return HttpResponse("上传失败!")
    filename = os.path.join(settings.MEDIA_ROOT, file.name)
    if not os.access(filename, os.F_OK):
        return HttpResponse("文件不存在!")
    book = pe.get_book(file_name=filename)
    i = 0
    v = ''
    for sheet in book:
        #if sheet.name == 'cmdb':
        sheet.name_columns_by_row(0) 
        records = sheet.to_records()
    if what == 'app':
        fields = [f for f in App._meta.fields]
        kw={}
        for record in records:
            for field in fields:
                v =  record[(field.verbose_name).decode(encoding='UTF-8',errors='strict')]
                if field.name == 'ip' and v == '':
                    continue
                kw[field.name] = v
            app=App(**kw)
            app.save()
        i = len(App.objects.all())
        app_temp = App_Temp.objects.get(id=1)
        app_temp.num_items = i
        app_temp.save()
    elif what == 'hardware':
        fields = [f for f in Hardware._meta.fields]
        kw = {}
        for record in records:
            for field in fields:
                v =  record[(field.verbose_name).decode(encoding='UTF-8',errors='strict')]
                if field.name == 'sn' and v == '':
                    continue
                kw[field.name] = v
            hd=Hardware(**kw)
            hd.save()
        i = len(Hardware.objects.all())
        hd_temp = Hardware_Temp.objects.get(id=1)
        hd_temp.num_items = i
        hd_temp.save()
    elif what == 'ipsn':
        fields = [f for f in Ip_Sn._meta.fields]
        kw = {}
        for record in records:
            for field in fields:
                if field.name != 'id':
                    kw[field.name] = record[(field.verbose_name).decode(encoding='UTF-8',errors='strict')]
            try:
                if kw['ip'] == '' or kw['sn'] == '':
                    continue
                ipsn=Ip_Sn(**kw)
                ipsn.save()
            except:
                return HttpResponse("重复数据(%s-%s)!"%(kw['ip'],kw['sn']))
        i = len(Ip_Sn.objects.all())
        ipsn_temp = Ip_Sn_Temp.objects.get(id=1)
        ipsn_temp.num_items = i
        ipsn_temp.save()
    else:
        pass
    return HttpResponse(True)
# ======================================================================
def asset_export(request,what):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    file=open('/var/www/html/cmdb.xls','rb')  
    response =HttpResponse(file)  
    response['Content-Type']='application/octet-stream'  
    response['Content-Disposition']='attachment;filename="cmmb.xls"'
    return response
    """
    if what == 'app':
        fields = [f for f in App._meta.fields]
        kw = {}
        for field in fields:
            kw[field.name] = request.POST.get(field.name, "")
        if not kw.get('ip',None):
            return error_page(request,"IP不能为空")
        if editmode != 'edit':
            app=App(**kw)
            app.save()
        else:
            app = App.objects.get(ip=kw['ip'])
            for k,v in kw.items():
                setattr(app, k , v)
            app.save()
    elif what == 'hardware':
        fields = [f for f in Hardware._meta.fields]
        kw = {}
        for field in fields:
            kw[field.name] = request.POST.get(field.name, "")
        if not kw.get('sn',None):
            return error_page(request,"序列号不能为空")
        if editmode != 'edit':
            hd=Hardware(**kw)
            hd.save()
        else:
            hd = Hardware.objects.get(sn=kw['sn'])
            for k,v in kw.items():
                setattr(hd, k , v)
            hd.save()
    elif what == 'ipsn':
        ip = request.POST.get('ip', "")
        sn = request.POST.get('sn', "")
        if sn == "" or ip == "":
            return error_page(request,"IP和序列号不能为空")
        if editmode != 'edit':
            ipsn=Ip_Sn(sn=sn,ip=ip)
            ipsn.save()
        else:
            ipsn = Ip_Sn.objects.get(ip=ip)
            ipsn.sn = sn
            ipsn.save()
    else:
        pass
    return HttpResponseRedirect('/quick/asset/%s/list'%what)
    """
# ======================================================================
def asset_edit(request,what,obj_name=None,editmode='edit'):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    action = request.GET.get('action', '')
    if what == 'app':
        fields = [f for f in App._meta.fields]
        if obj_name:
            item = App.objects.filter(ip=obj_name)
        else:
            item = ''
    elif what == 'hardware':
        fields = [f for f in Hardware._meta.fields]
        if obj_name:
            item = Hardware.objects.filter(sn=obj_name)
        else:
            item = ''
    elif what == 'ipsn':
        fields = [f for f in Ip_Sn._meta.fields]
        if obj_name:
            item = Ip_Sn.objects.filter(id=obj_name)
        else:
            item = ''
    else:
        item = ''
        fields = ''
    if editmode == 'edit':
        editable = False
    else:
        editable = True
    columns=[]
    for field in fields:
        columns.append([field.name,field.verbose_name])

    newitem = []
    if item == '':
        for name,verbose_name in columns:
            newitem.append([name,'','',verbose_name])
    else:
        for name,verbose_name in columns:
            newitem.append([name,getattr(item[0], name),'',verbose_name])
    t = get_template("asset_edit.tmpl")
    html = t.render(RequestContext(request,{
        'what'            : "asset/%s"%what,
        'action'          : action,
        'name'            : obj_name,
        'editmode'        : editmode,
        'editable'        : editable,
        'items'           : newitem,
        'username'        : request.session['username'],
        'menu'            : request.session['%s_menu'%request.session['username']]
    }))
    return HttpResponse(html)
# ======================================================================
@require_POST
@csrf_protect
def asset_delete(request,what,obj_name=None):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    if what == 'app':
        if obj_name:
            App.objects.get(ip=obj_name).delete()
            app_temp = App_Temp.objects.get(id=1)
            app_temp.num_items = str(int(app_temp.num_items) - 1)
            app_temp.save()
        else:
            return error_page(request,"未知操作")
    elif what == 'hardware':
        if obj_name:
            Hardware.objects.get(sn=obj_name).delete()
            hd_temp = Hardware_Temp.objects.get(id=1)
            hd_temp.num_items = str(int(hd_temp.num_items) - 1)
            hd_temp.save()
        else:
            return error_page(request,"未知操作")
    elif what == 'ipsn':
        if obj_name:
            Ip_Sn.objects.get(id=obj_name).delete()
            ipsn_temp = Ip_Sn_Temp.objects.get(id=1)
            ipsn_temp.num_items = str(int(ipsn_temp.num_items) - 1)
            ipsn_temp.save()
        else:
            return error_page(request,"未知操作")
    else:
        pass
    return HttpResponseRedirect("/quick/asset/%s/list"%what)
# ======================================================================

@require_POST
@csrf_protect
def asset_domulti(request,what,multi_mode=None,multi_arg=None):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    names = request.POST.get('names', '').strip().split()
    if names == "":
        return error_page(request, "未选中任何对象")
    if what == "app":
        if multi_mode == "delete" and multi_arg == 'delete':
            for name in names:
                App.objects.get(ip=name).delete()
            app_temp = App_Temp.objects.get(id=1)
            app_temp.num_items = str(int(app_temp.num_items) - len(names))
            app_temp.save()
        else:
            return error_page(request,"未知操作")
    elif what == "hardware":
        if multi_mode == "delete" and multi_arg == 'delete':
            for name in names:
                Hardware.objects.get(sn=name).delete()
            hd_temp = Hardware_Temp.objects.get(id=1)
            hd_temp.num_items = str(int(hd_temp.num_items) - len(names))
            hd_temp.save()
        else:
            return error_page(request,"未知操作")
    elif what == 'ipsn':
        if multi_mode == "delete" and multi_arg == 'delete':
            for name in names:
                Ip_Sn.objects.get(id=name).delete()
            ipsn_temp = Ip_Sn_Temp.objects.get(id=1)
            ipsn_temp.num_items = str(int(ipsn_temp.num_items) - len(names))
            ipsn_temp.save()
        else:
            return error_page(request,"未知操作")
    return HttpResponseRedirect("/quick/asset/%s/list"%what)
# ======================================================================
def modify_list(request, obj, what, pref, value=None):
    """
    本功能用于修改资产管理下各视图显示的条目数和条目排序准则
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/%s/%s/list"%(obj,what), expired=True)

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
    return HttpResponseRedirect("/quick/%s/%s/list" % (obj,what))
#==================================================================================

def host_list(request,what,page=None):
    """
    <主机管理>处理逻辑
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/host/%s/list"%what, expired=True)
    columns=[]
    groups = []
    scripts = []
    items = {}
    num_items = 0
    if page == None:
        page = int(request.session.get("%s_page" % what, 1))
    limit = int(request.session.get("%s_limit" % what, 10))
    sort_field = sort_field_old = request.session.get("%s_sort_field" % what, "name")
    if sort_field.startswith("!"):
        sort_field=sort_field.replace("!","-")
    filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))
    batchactions = [["删除","delete","delete"],]
    if what == 'single':
        osip = request.POST.get('osip', "").replace('\r\n','\n').strip()
        app_fields = [f for f in App._meta.fields]
        app_columns=[]
        for field in app_fields:
            app_columns.append([field.name,field.verbose_name,'on'])
        hd_fields = [f for f in Hardware._meta.fields]
        hd_columns=[]
        for field in hd_fields:
            hd_columns.append([field.name,field.verbose_name,'on'])
        hd_items=[]
        app_items=[]
        items = []
        if osip != '':
            app = App.objects.filter(ip=osip)
            if app:
                ipsn = Ip_Sn.objects.filter(ip=app[0].ip)
                app_items = __format_items(app,app_columns)
                if ipsn:
                    hd = Hardware.objects.filter(sn=ipsn[0].sn)
                    hd_items = __format_items(hd,hd_columns)
                    app_items.extend(hd_items)
                items = app_items
    else:
        if what == 'group':
            items = Host_Group.objects.filter(**filters).order_by(sort_field)
            num_items = len(items)
            offset = (page -1 )*limit
            end = page*limit
            items = Host_Group.objects.filter(**filters).order_by(sort_field)[offset:end]
            fields = [f for f in Host_Group._meta.fields]
            for field in fields:
                columns.append([field.name,field.verbose_name,'on'])
            items = __format_items(items,columns)
        elif what == 'script':
            items = Script.objects.filter(**filters).order_by(sort_field)
            num_items = len(items)
            offset = (page -1 )*limit
            end = page*limit
            items = Script.objects.filter(**filters).order_by(sort_field)[offset:end]
            fields = [f for f in Script._meta.fields]
            for field in fields:
                columns.append([field.name,field.verbose_name,'on'])
            items = __format_items(items,columns)
        elif what == 'batch':
            if request.GET.get("action", ""):
                """
                tasks = Batch_Temp.objects.all()
                for task in tasks:
                    if task.status !='' or task.result != '':
                        ip = task.ip
                        status = task.status
                        result = task.result
                        Batch_Temp.get(ip=ip).delete()
                        return HttpResponse([ip,status,result])
                """
                datas = request.session['testdata']
                if datas:
                    data = datas[0]
                    datas.pop(0)
                    request.session['testdata'] = datas
                    result = {"ip":data[0],"status":data[1],"result":data[2]}
                    return HttpResponse(simplejson.dumps(result,ensure_ascii=False),content_type="application/json,charset=utf-8")
                return HttpResponse([])
            elif request.POST.get("hosttype", ""):
                hosttype = request.POST.get("hosttype", "")
                scripttype = request.POST.get("scripttype", "")
                groupname = request.POST.get("groupname", "")
                scriptname = request.POST.get("scriptname", "")
                host_user = request.POST.get("username", "")
                host_pass = request.POST.get("password", "")
                #if groupname and scriptname and host_user and host_pass:
                    #return HttpResponse([hosttype,scripttype,groupname,scriptname,host_user,host_pass])
                    #something bachgroud_exec()
            else:
                testdata = [['192.168.1.5','success','haha'],['192.168.1.6','success','hahaha'],['192.168.1.7','failure','none']]
                request.session['testdata'] = testdata
                host_group = Host_Group.objects.all()
                for group in host_group:
                    groups.append(group.name)
                script = Script.objects.all()
                for s in script:
                    scripts.append(s.name)
    t = get_template("host_list.tmpl")
    #如果是https则为True，反之为False
    #request.is_secure()
    #获得当前的HTTP或HTTPS
    #http = urlsplit(request.build_absolute_uri(None)).scheme
    
    html = t.render(RequestContext(request,{
        'what'           : "host/%s"%what,
        'items'          : items,
        'location'       : request.META['HTTP_HOST'],
        'columns'        : __format_columns(columns,sort_field_old),
        'pageinfo'       : __paginate(num_items,page=page,items_per_page=limit),
        'filters'        : filters,
        'limit'          : limit,
        'username'       : request.session['username'],
        'batchactions'   : batchactions,
        'scripts'        : scripts,
        'groups'         : groups,
        'menu'           : request.session['%s_menu'%request.session['username']]
    }))
    return HttpResponse(html)

#==================================================================================
def host_edit(request,what,obj_name=None,editmode='edit'):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/host/%s/list"%what, expired=True)
    if what == 'group':
        fields = [f for f in Host_Group._meta.fields]
        if obj_name:
            item = Host_Group.objects.filter(name=obj_name)
        else:
            item = ''
    elif what == 'script':
        fields = [f for f in Script._meta.fields]
        if obj_name:
            item = Script.objects.filter(name=obj_name)
        else:
            item = ''
    if editmode == 'edit':
        editable = False
    else:
        editable = True
    columns=[]
    for field in fields:
        if field.name == 'create_time' or field.name== 'owner':
            continue
        columns.append([field.name,field.verbose_name])
    newitem = []
    if item == '':
        for name,verbose_name in columns:
            newitem.append([name,'','',verbose_name])
    else:
        for name,verbose_name in columns:
            newitem.append([name,getattr(item[0], name),'',verbose_name])
    t = get_template("host_edit.tmpl")
    html = t.render(RequestContext(request,{
        'what'            : "host/%s"%what,
        'name'            : "",
        'editmode'        : editmode,
        'editable'        : editable,
        'items'           : newitem,
        'username'        : request.session['username'],
        'menu'            : request.session['%s_menu'%request.session['username']]
    }))
    return HttpResponse(html)
#==================================================================================
@require_POST
@csrf_protect
def host_save(request,what,editmode='edit'):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/host/%s/list"%what, expired=True)
    editmode = request.POST.get('editmode', 'edit')
    if what == 'group':
        fields = [f for f in Host_Group._meta.fields]
        kw = {}
        for field in fields:
            if field.name == 'id' or field.name =='create_time' or field.name == 'owner':
                continue
            kw[field.name] = request.POST.get('host-%s'%field.name, "")
        if not kw.get('name',None):
            return error_page(request,"名称不能为空!")
        if editmode != 'edit':
            kw['create_time'] = time.time()
            kw['owner']       = request.session['username']
            hg=Host_Group(**kw)
            hg.save()
        else:
            objid = request.POST.get('host-id' "")
            hg = Host_Group.objects.get(id=objid)
            for k,v in kw.items():
                setattr(hg, k , v)
            hg.save()
    elif what == 'script':
        fields = [f for f in Script._meta.fields]
        kw = {}
        for field in fields:
            if field.name == 'id' or field.name =='create_time' or field.name == 'owner':
                continue
            kw[field.name] = request.POST.get('host-%s'%field.name, "")
        if not kw.get('name',None):
            return error_page(request,"名称不能为空!")
        if editmode != 'edit':
            kw['create_time'] = time.time()
            kw['owner']       = request.session['username']
            st=Script(**kw)
            st.save()
        else:
            objid = request.POST.get('host-id' "")
            st = Script.objects.get(id=objid)
            for k,v in kw.items():
                setattr(st, k , v)
            st.save()
    elif what == 'batch':
        pass
    else:
        return
    return HttpResponseRedirect('/quick/host/%s/list'%what)
#==================================================================================
def presence_list(request,page=None):
    pass
#==================================================================================
def presence_edit(request,sn=None, editmode='edit'):
    pass
#==================================================================================
def presence_save(request,editmode='edit'):
    pass
#==================================================================================
def virtual_list(request,page=None):
    pass
#==================================================================================
def ippool_list(request,page=None):
    """
    <资源管理>栏目下<地址池>处理逻辑
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/ippool/list", expired=True)
    what = 'ippool'
    if page == None:
        page = int(request.session.get("%s_page" % what, 1))
    limit = int(request.session.get("%s_limit" % what, 10))
    sort_field = sort_field_old = request.session.get("%s_sort_field" % what, "name")
    if sort_field.startswith("!"):
        sort_field=sort_field.replace("!","-")
    filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))
    batchactions = [["删除","delete","delete"],]
    items = Ip_Pool.objects.filter(**filters).order_by(sort_field)
    num_items = len(items)
    offset = (page -1 )*limit
    end = page*limit
    items = Ip_Pool.objects.filter(**filters).order_by(sort_field)[offset:end]
    columns=[]
    fields = [f for f in Ip_Pool._meta.fields]
    for field in fields:
        columns.append([field.name,field.verbose_name,'on'])

    t = get_template("ippool_list.tmpl")

    html = t.render(RequestContext(request,{
        'what'           : what,
        'columns'        : __format_columns(columns,sort_field_old),
        'items'          : __format_items(items,columns),
        'pageinfo'       : __paginate(num_items,page=page,items_per_page=limit),
        'filters'        : filters,
        'limit'          : limit,
        'username'       : request.session['username'],
        'batchactions'   : batchactions,
        'menu'           : request.session['%s_menu'%request.session['username']]
    }))
    return HttpResponse(html)
#==================================================================================
def ippool_edit(request,sn=None, editmode='edit'):
    pass
#==================================================================================
def ippool_save(request,editmode='edit'):
    pass
#==================================================================================
def storage_list(request,page=None):
    """
    <资源管理>栏目下<地址池>处理逻辑
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/storage/list", expired=True)
    pass
def storage_edit(request,sn=None, editmode='edit'):
    pass
#==================================================================================
def storage_save(request,editmode='edit'):
    pass

#==================================================================================
def __format_columns(column_names,sort_field):
    dataset = []
    # Default is sorting on name
    if sort_field is not None:
        sort_name = sort_field
    else:
        sort_name = ""

    if sort_name.startswith("!"):
        sort_name = sort_name[1:]
        sort_order = "desc"
    else:
        sort_order = "asc"
    i=0
    for fieldname,fieldverbosename,fieldstatus in column_names:
        i=i+1
        fieldorder = "none"
        if fieldname == sort_name:
            fieldorder = sort_order
        dataset.append([fieldname,fieldorder,fieldverbosename,i,fieldstatus])
    return dataset


#==================================================================================

def __format_items(items, column_names):
    """
    """
    dataset = []
    for itemhash in items:
        row = []
        for fieldname,fieldverbosename,fieldstatus in column_names:
            if fieldname == "ip":
                html_element = "editlink"
            elif fieldname == "sn":
                html_element = "editlink"
            else:
                html_element = "text"
            row.append([fieldname,itemhash.__dict__[fieldname],html_element,fieldverbosename,fieldstatus])
        dataset.append(row)
    return dataset
#==================================================================================
def __paginate(num_items=0,page=None,items_per_page=None,token=None):
    """
    Helper function to support returning parts of a selection, for
    example, for use in a web app where only a part of the results
    are to be presented on each screen.
    """
    default_page = 1
    default_items_per_page = 25

    try:
        page = int(page)
        if page < 1:
            page = default_page
    except:
        page = default_page
    try:
        items_per_page = int(items_per_page)
        if items_per_page <= 0:
            items_per_page = default_items_per_page
    except:
        items_per_page = default_items_per_page

    num_pages = ((num_items-1)/items_per_page)+1
    if num_pages==0:
        num_pages=1
    if page>num_pages:
        page=num_pages
    start_item = (items_per_page * (page-1))
    end_item   = start_item + items_per_page
    if start_item > num_items:
        start_item = num_items - 1
    if end_item > num_items:
        end_item = num_items

    if page > 1:
        prev_page = page - 1
    else:
        prev_page = "~"
    if page < num_pages:
        next_page = page + 1
    else:
        next_page = "~"
                    
    return ({
            'page'        : page,
            'prev_page'   : prev_page,
            'next_page'   : next_page,
            'pages'       : range(1,num_pages+1),
            'num_pages'   : num_pages,
            'num_items'   : num_items,
            'start_item'  : start_item,
            'end_item'    : end_item,
            'items_per_page' : items_per_page,
            'items_per_page_list' : [10,20,50,100,200,500],
            })













