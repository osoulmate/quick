#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from datetime import datetime
from django.contrib.sessions.models import Session
import simplejson
from quick.models import Users,Login_Log

@require_POST
@csrf_protect
def do_logout(request):
    try:
        meta = request.session['quick_meta']
        meta = simplejson.loads(meta)
        username = meta['username']
        Session.objects.filter(session_key=request.session.session_key).delete()
        now = datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        login_log = Login_Log(time=now,action='登出',user=username,status='成功',ip=request.META['REMOTE_ADDR'],remark='正常退出')
        login_log.save()
    except Exception,e:
        return HttpResponseRedirect("/quick")
    else:
        pass
    return HttpResponseRedirect("/quick")
#========================================================================
def do_logout_timeout(request):
    try:
        meta = request.session['quick_meta']
        meta = simplejson.loads(meta)
        username = meta['username']
        Session.objects.filter(session_key=request.session.session_key).delete()
        now = datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        login_log = Login_Log(time=now,action='登出',user=username,status='成功',ip=request.META['REMOTE_ADDR'],remark='超时退出')
        login_log.save()
    except Exception,e:
        return HttpResponseRedirect("/quick")
    else:
        pass
    return HttpResponseRedirect("/quick")



