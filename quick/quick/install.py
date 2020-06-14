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
from django.core.mail import EmailMultiAlternatives
import re
import time
import simplejson
import oauth
import utils
from login import login
from error_page import error_page
from quick.models import *
#========================================================================
@csrf_protect
def task_edit(request,task_name=None, editmode='edit'):
    """
    任务编辑或新建功能处理逻辑
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/install/resume/list", expired=True)
    tasks = []
    if editmode == 'edit':
        editable = False
        tasks = List.objects.filter(name=task_name)
        if tasks:
            tasks = tasks[0]
        else:
            return HttpResponseRedirect('/quick/install/resume/list')
    else:
        editable = True
    envs = [['reinstall-no-dhcp','无DHCP系统重装'],
            ['reinstall-dhcp','有DHCP系统重装'],
            ['newinstall-dhcp','有DHCP系统新装']
           ]
    osreleases=list()
    profiles=oauth.remote.get_profiles()
    for profile in profiles:
        osreleases.append(profile['name'])
    redhat=[]
    suse=[]
    ubuntu=[]
    archs=[]
    for osrelease in osreleases:
        if 'centos' in osrelease.lower() or 'redhat' in osrelease.lower():
            redhat.append(osrelease.lower().split('-')[0])
        elif 'suse' in osrelease.lower():
            suse.append(osrelease.lower().split('-')[0])
        elif 'ubuntu' in osrelease.lower():
            ubuntu.append(osrelease.lower().split('-')[0])
        else:
            pass
        archs.append(osrelease.lower().split('-')[1])
    redhat = list(set(redhat))
    suse   = list(set(suse))
    ubuntu = list(set(ubuntu))
    archs = list(set(archs))
    redhat.sort()
    suse.sort()
    ubuntu.sort()
    archs.sort()
    if redhat == [] and ubuntu == [] and suse == []:
        breeds = {}
    else:
        breeds = {"RedHat based(includes Fedora,CentOS,Scientific Linux)":redhat,"suse":suse,"ubuntu":ubuntu}
    t = get_template("task_edit.tmpl")
    html = t.render(RequestContext(request,{
        'breeds'            : breeds,
        'name'              : task_name,
        'osenvs'            : envs,
        'editmode'          : editmode,
        'editable'          : editable,
        'tasks'             : tasks,
        'osarch'            : archs,
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)
#========================================================================
def tasklist(request,what,page=None):
    """
    显示任务列表、任务详情、历史任务
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/install/%s/list"%what, expired=True)
    meta = simplejson.loads(request.session['quick_meta'])
    if page == None:
        page = int(request.session.get("%s_page" % what, 1))
    limit = int(request.session.get("%s_limit" % what, 10))
    sort_field = sort_field_old = request.session.get("%s_sort_field" % what, "name")
    if sort_field.startswith("!"):
        sort_field=sort_field.replace("!","-")
    filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))
    user = Users.objects.get(username=meta['username'])
    columns=[]
    if user.is_superuser=='no':
        filters['owner'] = meta['username']
    user_profile = User_Profile.objects.filter(username=meta['username'])
    if user_profile:
        user_profile = user_profile[0]
    else:
        return HttpResponse("unknown user view!")
    now = int(time.time())
    if what == "resume":
        include_columns = [ "name","ips","usetime","status","owner"]
        fields = [f for f in List._meta.fields]
        for field in fields:
            if field.name in include_columns:
                k = "install_%s"%field.name
                columns.append([field.name,field.verbose_name,getattr(user_profile,k,'on')])
            else:
                continue
        batchactions = [["删除","delete","delete"],]
        tasks = List.objects.filter(flag='resume',**filters).order_by(sort_field)
        t = "task_list.tmpl"

    if what == 'detail':
        include_columns = [ "name","ip","mac","hardware_model","hardware_sn","apply_template","usetime","status","owner","ipmi_ip"]
        fields = [f for f in Detail._meta.fields]
        for field in fields:
            if field.name in include_columns:
                k = "install_%s"%field.name
                columns.append([field.name,field.verbose_name,getattr(user_profile,k,'on')])
            else:
                continue
        batchactions = [["删除","delete","delete"],
                        ["开机","power","on"],
                        ["关机","power","off"],
                        ["重启","power","reboot"],
                        ["网络启动","pxe","boot"],
                       ]
        task_name = request.GET.get("name","")
        if task_name != '':
            filters['name'] = task_name
        else:
            if filters.has_key('name'):
                del filters['name']
        tasks = Detail.objects.filter(**filters).order_by(sort_field)
        t = "task_detail.tmpl"
    if what == 'history':
        include_columns = [ "name","ips","usetime","status","owner"]
        fields = [f for f in List._meta.fields]
        for field in fields:
            if field.name in include_columns:
                k = "install_%s"%field.name
                columns.append([field.name,field.verbose_name,getattr(user_profile,k,'on')])
            else:
                continue
        batchactions = [["删除","delete","delete"],]
        tasks = List.objects.filter(flag='history',**filters).order_by(sort_field)
        t = "task_history.tmpl"
    (items,pageinfo) = __paginate(tasks,page=page,items_per_page=limit)
    if filters.get('owner',''):
        del filters['owner']
    t = get_template(t)
    html = t.render(RequestContext(request,{
        'what'           : 'install/%s'%what,
        'columns'        : __format_columns(columns,sort_field_old),
        'items'          : __format_items(items,columns),
        'pageinfo'       : pageinfo,
        'filters'        : filters,
        'limit'          : limit,
        'batchactions'   : batchactions,
        'location'       : request.META['HTTP_HOST'],
        'meta'           : meta
    }))
    return HttpResponse(html)

#========================================================================
def task_save(request,editmode='edit'):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/install/save/%s" % task_name, expired=True)
    meta = simplejson.loads(request.session['quick_meta'])
    editmode = request.POST.get('editmode', 'edit')
    osip = request.POST.get('osip', "").replace('\n','').replace('\r','')
    if osip == '':
        return error_page(request, "IP地址不能为空")
    else:
        osuser = request.POST.get('osuser', "").replace('\n','').replace('\r','').replace(' ','')
        ospwd = request.POST.get('ospass', "")
        osarch = request.POST.get('osarch', "").replace('\n','').replace('\r','').replace(' ','')
        osbreed = request.POST.get('osbreed', "").replace('\n','').replace('\r','').replace(' ','')
        osrelease = request.POST.get('osrelease', "").replace('\n','').replace('\r','').replace(' ','')
        ospart = request.POST.get('ospart', "").replace('\n','').replace('\r','').replace(' ','')
        ospackages = request.POST.get('ospackages', "").replace('\n','').replace('\r','').replace(' ','')
        osenv = request.POST.get('osenv', "").replace('\n','').replace('\r','').replace(' ','')
        raid = request.POST.get('raid', "").replace('\n','').replace('\r','').replace(' ','')
        mail = request.POST.get('notice_mail', "").replace('\n','').replace('\r','').replace(' ','')
        path = request.POST.get('drive_path', "").replace('\n','').replace('\r','').replace(' ','')
        profile = osrelease+'-'+osarch
        if 'redhat' in osbreed.lower():
            osbreed = 'redhat'
    if editmode != 'edit':
        now = int(time.time())
        task_name = 'task_'+ str(now)
        task = List(name=task_name,ips=osip,osuser=osuser,ospwd=ospwd,osarch=osarch,osbreed=osbreed,
            osrelease=osrelease,ospart=ospart,ospackages=ospackages,osenv=osenv,raid=raid,start_time='0',
            usetime='0',status='任务初始化',notice_mail=mail,drive_path=path,owner=meta['username'],flag='resume')
        task.save()
        if osenv == 'reinstall-no-dhcp':
            utils.background_collect(task_name)
        else:
            utils.generate_data(osip,task_name,profile,'0','等待上线',meta['username'])
    else:
        name  = request.POST.get('name', "")
        task = List.objects.get(name=name)
        task.ips = osip
        task.osuser = osuser
        task.ospwd = ospwd
        task.osarch = osarch
        task.osbreed = osbreed
        task.osrelease = osrelease
        task.ospart = ospart
        task.ospackages = ospackages
        task.osenv = osenv
        task.raid = raid
        task.notice_mail = mail
        task.drive_path = path
        #task.start_time = '0'
        task.owner = meta['username']
        task.save()
        if osenv == 'reinstall-no-dhcp':
            utils.background_collect(name)
    return HttpResponseRedirect('/quick/install/resume/list')
#========================================================================
def task_execute(request,task_name=None):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/install/resume/list", expired=True)
    if task_name != None:
        now = int(time.time())
        task = List.objects.filter(name=task_name)
        ip_list = []
        if task:
            task = task[0]
            subtasks = Detail.objects.filter(name=task_name)
            if not subtasks:
                return error_page(request,"任务正在初始化，请稍等...")
            else:
                if len(subtasks) < len(utils.generate_ip_list(task.ips)):
                    return error_page(request,"任务尚未完成初始化，请稍后重试...")
                else:
                    for subtask in subtasks:
                        if subtask.usetime == '0':
                            ip_list.append(subtask.ip)
                            subtask.start_time = now
                            subtask.save()
            if task.osenv == 'reinstall-no-dhcp':
                utils.background_qios(task.name)
            else:
                utils.add_cobbler_system(oauth.remote,request.session['cobbler_token'],task_name,
                    task.ospart,task.ospackages,task.raid)
                oauth.remote.background_sync({"verbose":"True"},request.session['cobbler_token'])
            if task.usetime =='0':
                task.start_time = now
                task.status = '执行中...'
                task.save()
                utils.add_vnc_token(ip_list=ip_list)
            return HttpResponseRedirect('/quick/install/resume/list')
        else:
            return error_page(request,"任务不存在")
#========================================================================
def task_delete(request,what,task_name=None):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/install/%s/list" %what, expired=True)
    if task_name is None:
        return error_page(request, "请选择要删除的%s任务" % what)
    if what == 'history':
        tasks = List.objects.get(name=task_name).filter(flag='history')
        try:
            tasks.delete()
        except:
            return error_page(request,err)
    if what == 'resume':
        task = List.objects.get(name=task_name)
        task.flag = 'history'
        task.save()
        try:
            Detail.objects.filter(name=task_name).delete()
        except Exception,err:
            return error_page(request,err)
    if what == 'detail':
        try:
            Detail.objects.filter(name=task_name).delete()
        except Exception,err:
            return error_page(request,err)
    return HttpResponseRedirect("/quick/install/%s/list"%what)
#========================================================================
def task_state(request,task_name=None):
    now = int(time.time())
    action = request.GET.get('k','')
    progress='0'
    usetime='0'
    '''
    任务列表页面ajax请求处理逻辑
    '''
    if re.match('^(task_\d+$)',task_name):
        task = List.objects.filter(name=task_name,flag='resume')
        if task:
            task = task[0]
        else:
            return HttpResponse('False')
        progress = task.status
        if progress != '完成':
            if task.start_time == '0':
                usetime = '0'
            else:
                usetime = now - int(float(task.start_time))
                usetime = utils.timers(usetime)
                task.usetime = usetime
                task.save()
        else:
            usetime = task.usetime

    '''
    任务详情页面ajax请求处理逻辑
    '''
    if re.match('^(task_\d+)-((\d{1,3}\.){3}\d{1,3})$',task_name):
        name = task_name.split('-')[0]
        ip = task_name.split('-')[1]
        subtask = Detail.objects.filter(ip=ip,name=name)
        if subtask:
            subtask = subtask[0]
        else:
            return HttpResponse('False')
        progress=subtask.status
        if progress != '100%':
            if subtask.start_time == '0':
                usetime = '0'
            else:
                usetime = now - int(float(subtask.start_time))
                usetime = utils.timers(usetime)
                subtask.usetime = usetime
                subtask.save()
        else:
            usetime = subtask.usetime
    '''
    客户机操作系统安装进度状态更新请求处理逻辑
    '''
    if 'install_' in task_name:
        step={"install_finish":"100%"}
        remote_ip = request.META['REMOTE_ADDR']
        subtask = Detail.objects.filter(~Q(status='100%'),ip=remote_ip)
        if subtask:
            subtask = subtask[0]
            name    = subtask.name
            status= step.get(task_name,task_name.split('install_')[1])
            usetime = now - int(float(subtask.start_time))
            subtask.usetime= utils.timers(usetime)
            subtask.status=re.sub('~',' ',status)
            subtask.save()
            running = Detail.objects.filter(~Q(status='100%'),name=name)
            total = Detail.objects.filter(name=name)
            finished = Detail.objects.filter(status='100%',name=name)
            task = List.objects.filter(name=name)
            if task:
                task = task[0]
                if running:
                    usetime = now - int(float(task.start_time))
                    task.usetime = utils.timers(usetime)
                    task.status = '执行中(%s/%s)'%(len(finished),len(total))
                    task.save()
                else:
                    usetime = now - int(float(task.start_time))
                    task.usetime = utils.timers(usetime)
                    task.status = '完成'
                    mail        = task.notice_mail
                    name        = task.name
                    task.save()
                    if mail != '':
                        __mail(name,mail)
        return HttpResponse('True')
    '''
    PXE下裸机安装操作系统，客户机硬件信息同步更新请求处理逻辑
    '''
    if task_name == 'notice':
        ip = request.META['REMOTE_ADDR']
        vendor = request.GET.get('vendor','')
        product = request.GET.get('product','')
        ipmiip = request.GET.get('ipmiip','')
        sn = request.GET.get('sn','')
        subtasks = Detail.objects.filter(ip=ip)
        for subtask in subtasks:
            if subtask.ip == ip and subtask.hardware_model =='wait':
                vendor = re.sub('~',' ',vendor)
                product = re.sub('~',' ',product)
                sn = re.sub('~',' ',sn)
                ipmiip = re.sub('~',' ',ipmiip)
                subtask.vendor = vendor
                subtask.hardware_model = product
                subtask.hardware_sn = sn
                subtask.ipmi_ip = ipmiip
                subtask.save()
        return HttpResponse('True')
    if action == 'usetime':
        return HttpResponse(usetime)
    if action == 'progress':
        return HttpResponse(progress)
    return HttpResponse('False')
# ======================================================================

@require_POST
@csrf_protect
def task_domulti(request, what, multi_mode=None, multi_arg=None):
    ''' what in ['list','history'],no other'''
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/install/%s/list" %what, expired=True)

    names = request.POST.get('names', '').strip().split()
    if names == "":
        return error_page(request, "未选中任何'%s' 对象" % what)

    if what == "resume" and multi_mode == "delete":
        for name in names:
            task = List.objects.get(name=name)
            task.flag = 'history'
            task.save()
            try:
                Detail.objects.filter(name=name).delete()
            except:
                pass
            else:
                pass
    elif what == "history" and multi_mode == "delete":
        for name in names:
            List.objects.get(name=name).delete()
    elif what == "detail" and multi_mode == "delete":
        for name in names:
            try:
                Detail.objects.filter(ip=name).delete()
            except:
                pass
            else:
                pass
    else:
        return error_page(request,"未知操作")
    return HttpResponseRedirect("/quick/install/%s/list"%what)
# ======================================================================
def __format_columns(column_names,sort_field):
    """

    """
    dataset = []
    # Default is sorting on name
    if sort_field is not None:
        sort_name = sort_field
    else:
        sort_name = "name"

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
    dataset = []
    for itemhash in items:
        row = []
        for fieldname,fieldverbosename,fieldstatus in column_names:
            if fieldname == "name":
                html_element = "name"
            elif fieldname in [ "ip", "apply_template" ]:
                html_element = "editlink"
            else:
                html_element = "text"
            row.append([fieldname,itemhash.__dict__[fieldname],html_element,fieldverbosename,fieldstatus])
        dataset.append(row)
    return dataset

#==================================================================================
def __paginate(data,page=None,items_per_page=None,token=None):
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

    num_items = len(data)
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
    data = data[start_item:end_item]

    if page > 1:
        prev_page = page - 1
    else:
        prev_page = "~"
    if page < num_pages:
        next_page = page + 1
    else:
        next_page = "~"
                    
    return (data,{
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
def __mail(task_name,to):
    if to != '':
        if ";" in to:
            to = to.split(";")
        else:
            to = [to]
    else:
        return 0
    subtasks = Detail.objects.filter(name=task_name)
    apply_template = ""
    iplist = []
    if subtasks:
        for subtask in subtasks:
            iplist.append(subtask.ip)
            apply_template = subtask.apply_template
    subject, from_email = '装机任务完成通知', 'askqingya@163.com'
    text_content = ''
    html_content = '<p>您好！您创建的装机任务<strong>%s</strong>已完成</p><p>任务主机:%s</p><p>装机模板:%s</p>'%(task_name,iplist,apply_template)
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html")
    msg.send()
    return 1












