#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from datetime import datetime
import time
import base64
import xmlrpclib
import cobbler.utils as utils
from quick.models import Users
from login import login
import menu

@require_POST
@csrf_protect
def do_login(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    nextsite = request.POST.get('next',None)
    users = Users.objects.filter(username=username,password=password)
    if not users:
        return login(request,nextsite,message="用户名或密码错误")
    for user in users:
        if user.is_active == 'disable':
            return login(request,nextsite,message="您的账号尚未激活，请联系管理员")
        user.is_online = 'online'
        user.save()
    url_cobbler_api = utils.local_get_cobbler_api_url()
    remote = xmlrpclib.Server(url_cobbler_api, allow_none=True)

    shared_secret = utils.get_shared_secret()

    cobbler_token = remote.login("",shared_secret)
    if cobbler_token:

        request.session['username'] = username

        urandom = open("/dev/urandom")

        b64 = base64.encodestring(urandom.read(25))
        urandom.close()
        b64 = b64.replace("\n","")

        request.session[b64] = (time.time(), username)
        request.session['token'] = b64
        request.session['%s_menu'%username] = menu.menu
        request.session['cobbler_token'] = cobbler_token
        if nextsite:
           return HttpResponseRedirect(nextsite)
        else:
           return HttpResponseRedirect("/quick")
    else:
        return login(request,nextsite,message="登录失败，请重试")
