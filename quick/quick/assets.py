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
from datetime import datetime
import os
import re
import time
import uuid
import base64
import pyexcel as pe
import simplejson
import oauth
import utils
from login import login
from error_page import error_page
from quick.models import *

#========================================================================
def asset_list(request,what,page=None):
    """
    资产管理处理逻辑
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    meta = simplejson.loads(request.session['quick_meta'])
    if page == None:
        page = int(request.session.get("%s_page"%what, 1))
    limit = int(request.session.get("%s_limit"%what, 5))
    iplist = []
    columns=[]
    sort = ''
    if what == 'app':
        sort_field = request.session.get("%s_sort_field"%what, "ip")
    elif what == 'hardware':
        sort_field = request.session.get("%s_sort_field"%what, "sn")
    elif what == 'union':
        sort_field = request.session.get("%s_sort_field"%what, "ip")
    else:
        pass
    if sort_field.startswith("!"):
        sort =sort_field.replace("!","-")
    else:
        sort =sort_field
    filters = simplejson.loads(request.session.get("%s_filters"%what, "{}"))
    records = System.objects.filter(id=1)
    user_profile = User_Profile.objects.filter(username=meta['username'])
    if not records:
        return HttpResponse('no data!')
    else:
        records = records[0]
    batchactions = [["删除","delete","delete"],]
    ippool = request.session.get('%s_batch_query'%what, '').strip()
    if ippool:
        iplist = ippool.split("\n")
        request.session['%s_batch_query'%what] = ''
    if user_profile:
        user_profile = user_profile[0]
    else:
        return HttpResponse("unknown user view!")
    if what == 'app':
        fields = [f for f in App._meta.fields]
        if iplist:
            num_items = len(iplist)
            q = Q()
            q.connector = 'OR'
            for ip in iplist:
                q.children.append(("ip",ip))
            #items = App.objects.filter(q).order_by("ip")
            items = App.objects.filter(q)
        else:
            if not filters:
                num_items = records.app_records
            else:
                items = App.objects.filter(**filters).order_by(sort)
                num_items = len(items)
            offset = (page -1 )*limit
            end = page*limit
            items = App.objects.filter(**filters).order_by(sort)[offset:end]
        #json_data = serializers.serialize("json", items)
        #request.session["app_json_data"] = json_data
        for field in fields:
            if field.name == 'uuid' or field.name == 'ipmi_ip' or field.name == 'hardware_uuid' or field.name == 'remark':
                k = "%s_%s"%(what,field.name)
            else:
                k = field.name
            columns.append([field.name,field.verbose_name,getattr(user_profile,k,'on')])
        items = __format_items(items,columns)
        columns = __format_columns(columns,sort_field)
    elif what == 'hardware':
        fields = [f for f in Hardware._meta.fields]
        if iplist:
            num_items = len(iplist)
            q = Q()
            q.connector = 'OR'
            for sn in iplist:
                q.children.append(("sn",sn.strip()))
            #items = Hardware.objects.filter(q).order_by("sn")
            items = Hardware.objects.filter(q)
        else:
            if not filters:
                num_items = records.hardware_records
            else:
                items = Hardware.objects.filter(**filters).order_by(sort)
                num_items = len(items)
            offset = (page -1 )*limit
            end = page*limit
            items = Hardware.objects.filter(**filters).order_by(sort)[offset:end]
        for field in fields:
            if field.name == 'uuid' or field.name == 'ipmi_ip' or field.name == 'remark':
                k = "%s_%s"%(what,field.name)
            else:
                k = field.name
            columns.append([field.name,field.verbose_name,getattr(user_profile,k,'on')])
        items = __format_items(items,columns)
        columns = __format_columns(columns,sort_field)
    elif what == 'union':
        app_columns = []
        exculde = ['uuid','hardware_uuid','remark']
        fields = [f for f in App._meta.fields]
        for field in fields:
            k = "yw_view_%s"%field.name
            if field.name in exculde:
                continue
            app_columns.append([field.name,field.verbose_name,getattr(user_profile,k,'on')])

        hd_columns = []
        fields1 = [f for f in Hardware._meta.fields]
        for field in fields1:
            k = "yw_view_%s"%field.name
            if field.name in exculde:
                continue
            if field.name == 'ipmi_ip':
                continue
            hd_columns.append([field.name,field.verbose_name,getattr(user_profile,k,'on')])

        if iplist:
            num_items = len(iplist)
            q = Q()
            q.connector = 'OR'
            for ip in iplist:
                q.children.append(("ip",ip))
            app_items = App.objects.filter(q).order_by("ip")
        else:
            if not filters:
                num_items = records.app_records
            else:
                items = App.objects.filter(**filters).order_by(sort)
                num_items = len(items)
            offset = (page -1 )*limit
            end = page*limit
            app_items = App.objects.filter(**filters).order_by(sort)[offset:end]

        hd_items = []
        items = []
        for app_item in app_items:
            temp = []
            hd_item = Hardware.objects.filter(uuid=app_item.hardware_uuid)
            app_item = __format_items([app_item],app_columns)
            if hd_item:
                hd_item = __format_items(hd_item,hd_columns)
                item = app_item[0] + hd_item[0]
            else:
                item = app_item[0]
            items.append(item)
        hd_columns = __format_columns(hd_columns,sort_field)
        app_columns = __format_columns(app_columns,sort_field)
        app_columns.extend(hd_columns)
        columns = app_columns
    else:
        pass
    t = get_template("asset_list.tmpl")

    html = t.render(RequestContext(request,{
        'what'           : "asset/%s"%what,
        'columns'        : columns,
        'items'          : items,
        'pageinfo'       : __paginate(num_items,page=page,items_per_page=limit),
        'filters'        : filters,
        'limit'          : limit,
        'location'       : request.META['HTTP_HOST'],
        'batchactions'   : batchactions,
        'meta'           : meta
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
    records = System.objects.filter(id=1)
    urandom = open("/dev/urandom")
    salt = base64.encodestring(urandom.read(25)) + str(time.time())
    if not records:
        return HttpResponse('no data!')
    else:
        records = records[0]
    try:
        if what == 'app':
            fields = [f for f in App._meta.fields]
            kw = {}
            for field in fields:
                if field.name == "uuid":
                    continue
                kw[field.name] = request.POST.get(field.name, "")
            if not kw.get('ip',None):
                ippool = request.POST.get("ippool", "")
                if ippool:
                    iplist = ippool.strip().split("\r\n")
                    for field in fields:
                        if field.name == 'uuid':
                            continue
                        if not kw.get(field.name,None):
                            kw.pop(field.name)
                else:
                    return error_page(request,"IP不能为空")
            if editmode != 'edit':
                #单个新增
                kw['uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,salt))).replace("-","")
                app=App(**kw)
                app.save()
                records.app_records = records.app_records + 1
                records.save()
            else:
                if iplist:
                    #批量更新
                    for ip in iplist:
                        app = App.objects.get(ip=ip)
                        for k,v in kw.items():
                            setattr(app, k , v)
                        app.save()
                else:
                    #单个更新
                    app = App.objects.get(ip=kw['ip'])
                    if kw['ipmi_ip'] == 'N/R' or kw['ipmi_ip'] == '':
                        #IPMI地址不存在的APP表记录，其字段名'hardware_id'的值
                        kw['ipmi_ip'] = 'N/R'
                        kw['hardware_uuid'] = 'N/R'
                    else:
                        #IPMI地址存在的APP表记录，其字段名'hardware_id'的值
                        if utils.is_valid_ip(kw['ipmi_ip']):
                            kw['hardware_uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,str(kw['ipmi_ip'])))).replace("-","")
                        else:
                            return error_page(request,'无效的IP地址！')
                    for k,v in kw.items():
                        setattr(app, k , v)
                    app.save()
        elif what == 'hardware':
            fields = [f for f in Hardware._meta.fields]
            kw = {}
            for field in fields:
                if field.name == "uuid":
                    continue
                kw[field.name] = request.POST.get(field.name,None)
            if not kw.get('sn',None):
                snpool = request.POST.get("snpool", "")
                if snpool:
                    snlist = snpool.strip().split('\r\n')
                    for field in fields:
                        if field.name == 'uuid':
                            continue
                        if not kw.get(field.name,None):
                            kw.pop(field.name)
                else:
                    return error_page(request,"序列号不能为空")
            if editmode != 'edit':
                #单个新增 ,可增加IP地址合法性检查
                if kw['ipmi_ip'] == 'N/R' or kw['ipmi_ip'] == '':
                    kw['ipmi_ip'] = 'N/R'
                    kw['uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,salt))).replace("-","")
                else:
                    kw['uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,str(kw['ipmi_ip'])))).replace("-","")
                hd=Hardware(**kw)
                hd.save()
                records.hardware_records = records.hardware_records + 1
                records.save()
            else:
                if snlist:
                    #批量更新
                    for sn in snlist:
                        try:
                            hd = Hardware.objects.get(sn=sn.strip())
                            for k,v in kw.items():
                                setattr(hd, k , v)
                            hd.save()
                        except Exception,e:
                            return error_page(request,str(e))
                else:
                    #单个更新
                    hd = Hardware.objects.get(sn=kw['sn'])
                    if hd.ipmi_ip != kw['ipmi_ip']:
                        if utils.is_valid_ip(kw['ipmi_ip']):
                            kw['uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,str(kw['ipmi_ip'])))).replace("-","")
                            is_exist = Hardware.objects.filter(uuid=kw['uuid'])
                            if is_exist:
                                return error_page(request,'重复的带外地址！')
                            for field in fields:
                                if field.name == "uuid" or field.name == 'ipmi_ip':
                                    continue
                                kw[field.name] = getattr(hd,field.name,'NULL')
                            Hardware.objects.get(sn=kw['sn']).delete()
                        else:
                            return error_page(request,'无效的IP地址！')
                    for k,v in kw.items():
                        setattr(hd, k , v)
                    hd.save()
        elif what == 'union':
            pass
        else:
            pass
    except Exception,e:
        raise
        return error_page(request,str(e))
    else:
        return HttpResponseRedirect('/quick/asset/%s/list'%what)
# ======================================================================
@require_POST
@csrf_protect
def asset_import(request,what):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    file = request.FILES['xlsfile']
    if file:
        if '.' not in file.name:
            return HttpResponse("上传文件格式错误（仅支持xls格式文件）!")
        if file.name.split('.')[1] != 'xls':
            return HttpResponse("上传文件格式错误（仅支持xls格式文件）!")
        else:
            filepath = os.path.join(settings.MEDIA_ROOT, file.name)
            try:
                with open(str(filepath),'wb') as f:
                    for info in file.chunks():
                        f.write(info)
            except Exception,e:
                return HttpResponse(str(e))
    else:
        return HttpResponse("上传文件不能位空!")
    filename = os.path.join(settings.MEDIA_ROOT, file.name)
    if not os.access(str(filename), os.F_OK):
        return HttpResponse("文件不存在!")
    book = pe.get_book(file_name=str(filename))
    urandom = open("/dev/urandom")
    salt = base64.encodestring(urandom.read(25)) + str(time.time())
    i = 0
    v = ''
    try:
        for sheet in book:
            #if sheet.name == 'cmdb':
            sheet.name_columns_by_row(0) 
            records = sheet.to_records()
        if what == 'app':
            fields = [f for f in App._meta.fields]
            kw={}
            for record in records:
                for field in fields:
                    v =  record.get((field.verbose_name).decode(encoding='UTF-8',errors='strict'),'N/R')
                    if field.name == 'ip' and v == '':
                        return HttpResponse('存在业务IP为空的记录，导入失败！')
                    if not v:
                        v = 'N/R'
                    kw[field.name] = v
                if kw['ipmi_ip'] == 'N/R' or kw['ipmi_ip'] == '':
                    #IPMI地址不存在的APP表记录，其字段名'hardware_id'的值
                    kw['ipmi_ip'] = 'N/R'
                    kw['hardware_uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,salt))).replace("-","")
                else:
                    #IPMI地址存在的APP表记录，其字段名'hardware_id'的值
                    kw['hardware_uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,str(kw['ipmi_ip'])))).replace("-","")
                try:
                    salt = base64.encodestring(urandom.read(25)) + str(time.time())
                    kw['uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,salt))).replace("-","")
                    app=App(**kw)
                    app.save()
                except Exception,e:
                    i = len(App.objects.all())
                    app_temp = System.objects.get(id=1)
                    app_temp.app_records = i
                    app_temp.save()
                    return HttpResponse([str(e),kw,'异常2'])
            i = len(App.objects.all())
            app_temp = System.objects.get(id=1)
            app_temp.app_records = i
            app_temp.save()
        elif what == 'hardware':
            fields = [f for f in Hardware._meta.fields]
            kw = {}
            for record in records:
                for field in fields:
                    v =  record.get((field.verbose_name).decode(encoding='UTF-8',errors='strict'),'N/R')
                    #忽略SN为空的记录
                    if field.name == 'sn' and v == '':
                        return HttpResponse('存在序列号为空的记录，导入失败！')
                    if not v:
                        v = 'N/R'
                    kw[field.name] = v
                if kw['ipmi_ip'] == '' or kw['ipmi_ip'] == 'N/R':
                    kw['ipmi_ip'] = 'N/R'
                    salt = base64.encodestring(urandom.read(25)) + str(time.time())
                    kw['uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,salt))).replace("-","")
                else:
                    kw['uuid'] = (str(uuid.uuid3(uuid.NAMESPACE_DNS,str(kw['ipmi_ip'])))).replace("-","")
                try:
                    hd=Hardware(**kw)
                    hd.save()
                except Exception,e:
                    i = len(Hardware.objects.all())
                    hd_temp = System.objects.get(id=1)
                    hd_temp.hardware_records = i
                    hd_temp.save()
                    return HttpResponse([str(e),kw,'异常2'])
            i = len(Hardware.objects.all())
            hd_temp = System.objects.get(id=1)
            hd_temp.hardware_records = i
            hd_temp.save()
        else:
            return HttpResponse('未知请求！')
    except Exception,e:
        return HttpResponse([str(e),'全局异常'])
    else:
        return HttpResponse(True)
# ======================================================================
def asset_export(request,what):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    app_items  = App.objects.all()
    app_fields = [f for f in App._meta.fields]
    hd_fields  = [f for f in Hardware._meta.fields]
    save_data = []
    try:
        for app_item in app_items:
            kw = {}
            q = Q()
            q.connector = 'OR'
            q.children.append(("ipmi_ip",app_item.ipmi_ip))
            q.children.append(("ipmi_ip",app_item.ip))
            hd_item = Hardware.objects.filter(q)
            for app_field in app_fields:
                k = (app_field.verbose_name).decode(encoding='UTF-8',errors='strict')
                v = getattr(app_item,app_field.name,'')
                kw[k] = v
            if hd_item:
                for hd_field in hd_fields:
                    k = (hd_field.verbose_name).decode(encoding='UTF-8',errors='strict')
                    v = getattr(hd_item[0],hd_field.name,'')
                    kw[k] =v 
            save_data.append(kw)
            #order_output = [u"设备类型",u"资产编号",u"地域",u"所属机房名称",u"机房编号",u"机柜编号",u"设备功能",u"设备型号",u"设备角色",u"序列号","U位","IPMI地址","运维地址","业务IP","硬件配置","设备生产商","所属项目","是否采购维保","维保开始时间","维保结束时间","维保厂家","使用人","业务模块","业务系统","项目简称","集群","操作系统","主机型号","CPU型号","CPUcore（总）","CPU主频(单位GHZ)","内存容量(单位G)","内置硬盘容量(单位G)","MirrorDisk状态","FW版本","电源个数","风扇个数","内核版本","是否已虚拟化","备注","是否资源池化","网卡是否已绑定","是否安全加固","防火墙是否已关闭","ssh是否已升级 ","项目编号","上架日期","服务IP1地址","服务IP2地址","服务实例名","一级业务系统","二级业务系统","三级业务系统","运维接口人","运维团队","开发接口人","开发团队","业务接口人","业务部门","监控系统","是否为CDN设备","生命周期状态","环境","结算运维接口人","结算使用人","UUID","上联架顶","业务IP来源","云管来源IP","访问区","结算部门","IPV6信息","[属于]合同","节点类型"]
        save_name = 'cmdb-%s.xls'%(str(datetime.now()).split(".")[0].replace(" ","").replace(":","").replace("-",""))
        filename = os.path.join(settings.MEDIA_ROOT, save_name)
        pe.save_as(records=save_data, dest_file_name=filename)
        file=open(filename,'rb')
    except Exception,e:
        return HttpResponse(str(e))
    else:
        response =HttpResponse(file)  
        response['Content-Type']='application/octet-stream'  
        response['Content-Disposition']='attachment;filename="%s"'%save_name
        return response

# ======================================================================
def asset_edit(request,what,obj_name=None,editmode='edit'):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    action = request.GET.get('action', '')
    if what == 'app':
        fields = [f for f in App._meta.fields]
        if obj_name:
            item = App.objects.filter(uuid=obj_name)
        else:
            item = ''
    elif what == 'hardware':
        fields = [f for f in Hardware._meta.fields]
        if obj_name:
            item = Hardware.objects.filter(uuid=obj_name)
        else:
            item = ''
    else:
        item = ''
        fields = ''
    if editmode == 'edit':
        editable = False
    else:
        editable = True
    if action == 'batch':
        editmode = 'edit'
        editable = False
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
        'meta'            : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)
# ======================================================================
@require_POST
@csrf_protect
def asset_delete(request,what,obj_name=None):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/asset/%s/list"%what, expired=True)
    if not obj_name:
        return HttpResponse("参数不能为空")
    try:
        if what == 'app':
            App.objects.get(uuid=obj_name).delete()
            app_temp = System.objects.get(id=1)
            app_temp.app_records = app_temp.app_records - 1
            app_temp.save()
        elif what == 'hardware':
            Hardware.objects.get(uuid=obj_name).delete()
            hd_temp = System.objects.get(id=1)
            hd_temp.hardware_records = hd_temp.hardware_records - 1
            hd_temp.save()
        else:
            pass
    except Exception,e:
        return HttpResponse(str(e))
    else:
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
    try:
        if what == "app":
            if multi_mode == "delete" and multi_arg == 'delete':
                for name in names:
                    App.objects.get(uuid=name).delete()
                app_temp = System.objects.get(id=1)
                app_temp.app_records = app_temp.app_records - len(names)
                app_temp.save()
            else:
                return error_page(request,"未知操作")
        elif what == "hardware":
            if multi_mode == "delete" and multi_arg == 'delete':
                for name in names:
                    Hardware.objects.get(uuid=name).delete()
                hd_temp = System.objects.get(id=1)
                hd_temp.hardware_records = hd_temp.hardware_records - len(names)
                hd_temp.save()
            else:
                return error_page(request,"未知操作")
    except Exception,e:
        return HttpResponse(str(e))
    return HttpResponseRedirect("/quick/asset/%s/list"%what)
# ======================================================================
def modify_list(request, obj, what, pref, value=None):
    """
    本功能用于修改资产管理下各视图显示的条目数和条目排序准则
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/%s/%s/list"%(obj,what), expired=True)

    if pref == "sort":

        old_sort = request.session.get("%s_sort_field" % what,"")
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
    meta = simplejson.loads(request.session['quick_meta'])
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
            if field.name == 'ipmi_ip' or field.name == 'uuid':
                continue
            hd_columns.append([field.name,field.verbose_name,'on'])
        hd_items=[]
        app_items=[]
        items = []
        if osip != '':
            app = App.objects.filter(ip=osip)
            if app:
                app_items = __format_items(app,app_columns)
                hd = Hardware.objects.filter(uuid=app[0].hardware_uuid)
                hd_items = __format_items(hd,hd_columns)
                items = app_items + hd_items
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
                iplist = request.session.get('batch_iplist',None)
                batch_name = request.session.get('batch_name',None)
                if iplist and batch_name:
                    for ip in iplist:
                        batch = Batch_Temp.objects.filter(name=batch_name,ip=ip)
                        if batch:
                            result = {"ip":ip,"status":batch[0].status,"result":batch[0].result}
                            iplist.pop(0)
                            request.session['batch_iplist'] = iplist
                            return HttpResponse(simplejson.dumps(result,ensure_ascii=False),content_type="application/json,charset=utf-8")
                        else:
                            return HttpResponse([[]])
                else:
                    request.session['batch_name'] = ''
                    request.session['batch_iplist'] = ''
                    return HttpResponse([[]])
            elif request.POST.get("hosttype", ""):
                host_group = Host_Group.objects.all()
                for group in host_group:
                    groups.append(group.name)
                script = Script.objects.all()
                for s in script:
                    scripts.append(s.name)
                hosttype = request.POST.get("hosttype", "")
                scripttype = request.POST.get("scripttype", "")
                multi_ip     = request.POST.get("batch_multi_host", "")
                script_name = request.POST.get("batch_script", "")
                host_user = request.POST.get("username", "")
                host_pass = request.POST.get("password", "")
                single_ip =  request.POST.get("batch_host", "")
                cmd = request.POST.get("batch_cmd", "")
                #return HttpResponse([[hosttype,scripttype,multi_ip,script_name,host_user,host_pass,cmd,single_ip]])
                if not host_user or not host_pass:
                    return error_page(request,'用户名、密码不能为空!')
                if single_ip and cmd and hosttype == '0' and scripttype == '0':
                    is_ip = 'yes'
                    ip_name = single_ip.strip()
                    script_name = cmd
                    request.session['batch_iplist'] = [ip_name]
                    ip_name = single_ip.strip()
                    is_script = 'no'
                elif single_ip and script_name and hosttype == '0' and scripttype == '1':
                    is_ip = 'yes'
                    ip_name = single_ip.strip()
                    request.session['batch_iplist'] = [ip_name]
                    is_script = 'yes'
                elif multi_ip and cmd and hosttype == '1' and scripttype == '0':
                    is_ip = 'no'
                    ips = Host_Group.objects.filter(name=multi_ip)
                    script_name = cmd
                    ip_name = multi_ip
                    if ips:
                        request.session['batch_iplist'] = (ips[0].content).split("\r\n")
                        is_script = 'no'
                    else:
                        return error_page(request,'未知主机组!')
                elif multi_ip and script_name and hosttype == '1' and scripttype == '1':
                    is_ip = 'no'
                    ips = Host_Group.objects.filter(name=multi_ip)
                    ip_name = multi_ip
                    if ips:
                        request.session['batch_iplist'] = (ips[0].content).split("\r\n")
                        is_script = 'yes'
                    else:
                        return error_page(request,'未知主机组!')
                else:
                    return error_page(request,'无效请求')
                batch_name = 'batch_%s'%(str(int(time.time())))
                request.session['batch_name'] = batch_name
                batch = Batch(name=batch_name,ip_name=ip_name,script_name=script_name,
                               osuser=host_user,ospwd=host_pass,owner=meta['username'],
                               is_ip=is_ip,is_script=is_script)
                batch.save()
                utils.background_exec(batch_name)
            else:
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
        'batchactions'   : batchactions,
        'scripts'        : scripts,
        'groups'         : groups,
        'meta'           : meta
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
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)
#==================================================================================
@require_POST
@csrf_protect
def host_save(request,what,editmode='edit'):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/host/%s/list"%what, expired=True)
    meta = simplejson.loads(request.session['quick_meta'])
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
            kw['owner']       = meta['username']
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
            kw['owner']       = meta['username']
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
        'batchactions'   : batchactions,
        'meta' : simplejson.loads(request.session['quick_meta'])
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
            if fieldname == "ip" or fieldname == "sn":
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
            'items_per_page_list' : [5,10,20,50,100,200,500],
            })











