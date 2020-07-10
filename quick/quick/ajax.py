#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import simplejson
import oauth
from login import login
from error_page import error_page
from quick.models import *
#========================================================================
@require_POST
@csrf_protect
def ajax(request):
    """
    json_data = request.session.get("%s_json_data"%what,"")
    if json_data:
        return HttpResponse(json_data)
    else:
        return HttpResponse('')
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick", expired=True)
    meta = simplejson.loads(request.session['quick_meta'])
    what  = request.POST.get('what', '')
    action = request.POST.get('action', '')
    try:
        if what == 'asset/app':
            if action == 'update_view_col':
                k = request.POST.get('name', '')
                v = request.POST.get('view', '')
                if k !='' and v != '':
                    special_col = ['uuid','ipmi_ip','remark','hardware_uuid']
                    if k in special_col:
                        k = 'app_%s'%k
                    app_temp = User_Profile.objects.get(username=meta['username'])
                    setattr(app_temp,k,v)
                    app_temp.save()
            elif action == 'batch_query':
                pool = request.POST.get('pool', '')
                if pool != '':
                    request.session['app_batch_query'] = pool
        elif what == 'asset/hardware':
            if action == 'update_view_col':
                k = request.POST.get('name', '')
                v = request.POST.get('view', '')
                if k !='' and v != '':
                    special_col = ['uuid','ipmi_ip','remark']
                    if k in special_col:
                        k = 'hardware_%s'%k
                    hd_temp = User_Profile.objects.get(username=meta['username'])
                    setattr(hd_temp,k,v)
                    hd_temp.save()
            elif action == 'batch_query':
                pool = request.POST.get('pool', '')
                if pool != '':
                    request.session['hardware_batch_query'] = pool
        elif what == 'asset/union':
            if action == 'update_view_col':
                k = request.POST.get('name', '')
                v = request.POST.get('view', '')
                if k !='' and v != '':
                    k = 'yw_view_%s'%k
                    yw_temp = User_Profile.objects.get(username=meta['username'])
                    setattr(yw_temp,k,v)
                    yw_temp.save()
            elif action == 'batch_query':
                pool = request.POST.get('pool', '')
                if pool != '':
                    request.session['union_batch_query'] = pool
        elif what == 'install/detail':
            if action == 'update_view_col':
                k = request.POST.get('name', '')
                v = request.POST.get('view', '')
                if k !='' and v != '':
                    k = 'install_%s'%k
                    task = User_Profile.objects.get(username=meta['username'])
                    setattr(task,k,v)
                    task.save()
        elif what == 'presence':
            if action == 'update_view_col':
                k = request.POST.get('name', '')
                v = request.POST.get('view', '')
                if k !='' and v != '':
                    k = 'esxi_host_%s'%k
                    task = User_Profile.objects.get(username=meta['username'])
                    setattr(task,k,v)
                    task.save()
        elif what == 'virtual':
            if action == 'update_view_col':
                k = request.POST.get('name', '')
                v = request.POST.get('view', '')
                if k !='' and v != '':
                    k = 'vm_host_%s'%k
                    task = User_Profile.objects.get(username=meta['username'])
                    setattr(task,k,v)
                    task.save()
        elif what == 'myinfo':
            if action == 'setup':
                header_style = request.POST.get('header',None)
                body_style = request.POST.get('body',None)
                style = User_Profile.objects.get(username=meta['username'])
                if header_style:
                    setattr(style,'topbar',header_style)
                    style.save()
                if body_style:
                    setattr(style,'background',body_style)
                    style.save()
    except Exception,e:
        return HttpResponse(str(e))
    else:
        return HttpResponse('ok')





