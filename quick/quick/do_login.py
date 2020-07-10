#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.sessions.models import Session
from datetime import datetime
import simplejson
import time
import base64
import xmlrpclib
import hashlib
import cobbler.utils as utils
from quick.models import Users,User_Profile,Login_Log,User_Right,User_Group,Group_Right,Rights
from login import login
#import menu

@require_POST
@csrf_protect
def do_login(request):
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    nextsite = request.POST.get('next',None)
    users = Users.objects.filter(username=username,password=hashlib.md5(password.encode(encoding='UTF-8')).hexdigest())
    now = datetime.now()
    now = now.strftime("%Y-%m-%d %H:%M:%S")
    if not users:
        login_log = Login_Log(time=now,action='登入',user=username,status='失败',ip=request.META['REMOTE_ADDR'],remark='用户名或密码错误')
        login_log.save()
        return login(request,nextsite,message="用户名或密码错误")
    else:
        user = users[0]
        if user.is_active == 'no':
            login_log = Login_Log(time=now,action='登入',user=username,status='失败',ip=request.META['REMOTE_ADDR'],remark='用户账号未激活')
            login_log.save()
            return login(request,nextsite,message="您的账号尚未激活，请联系管理员")
        if user.is_superuser == 'yes':
            rights = Rights.objects.all().order_by('id')
            kw = {}
            have_right = []
            menu = []
            order = []
            for right in rights:
                if right.desc == 'menu':
                    if kw.has_key(right.menu1_title):
                        kw[right.menu1_title]["children"].append({"title":right.menu2_title,"url":right.menu2_url,"menustate":"inactive"})
                    else:
                        kw[right.menu1_title] = {"menutitle":right.menu1_title,"menuicon":right.menu1_icon,"menustate":"inactive","children":[{"title":right.menu2_title,"url":right.menu2_url,"menustate":"inactive"}]}
                        order.append(right.menu1_title)
                have_right.append(right.menu2_url)
        else:
            kw = {}
            have_right = []
            menu = []
            order = []
            user_group = User_Group.objects.filter(user_id=user.id)
            if user_group:
                for group in user_group:
                    group_right = Group_Right.objects.filter(group_id=group.group_id)
                    for right in group_right:
                        right = Rights.objects.get(id=right.right_id)
                        if right.desc == 'menu':
                            if kw.has_key(right.menu1_title):
                                kw[right.menu1_title]["children"].append({"title":right.menu2_title,"url":right.menu2_url,"menustate":"inactive"})
                            else:
                                kw[right.menu1_title] = {"menutitle":right.menu1_title,"menuicon":right.menu1_icon,"menustate":"inactive","children":[{"title":right.menu2_title,"url":right.menu2_url,"menustate":"inactive"}]}
                                order.append(right.menu1_title)
                        have_right.append(right.menu2_url)
            user_right = User_Right.objects.filter(user_id=user.id)
            if user_right:
                for right in user_right:
                    right = Rights.objects.get(id=right.right_id)
                    if right.desc == 'menu':
                        if kw.has_key(right.menu1_title):
                            kw[right.menu1_title]["children"].append({"title":right.menu2_title,"url":right.menu2_url,"menustate":"inactive"})
                        else:
                            kw[right.menu1_title] = {"menutitle":right.menu1_title,"menuicon":right.menu1_icon,"menustate":"inactive","children":[{"title":right.menu2_title,"url":right.menu2_url,"menustate":"inactive"}]}
                            order.append(right.menu1_title)
                    have_right.append(right.menu2_url)
            else:
                if not user_group and user.is_superuser == 'no':
                    return login(request,nextsite,message="权限不足")
        for k in order:
            menu.append(kw[k])

    url_cobbler_api = utils.local_get_cobbler_api_url()
    remote = xmlrpclib.Server(url_cobbler_api, allow_none=True)

    shared_secret = utils.get_shared_secret()
    cobbler_token = remote.login("",shared_secret)
    if cobbler_token:
        urandom = open("/dev/urandom")
        b64 = base64.encodestring(urandom.read(25))
        urandom.close()
        b64 = b64.replace("\n","")
        request.session[b64] = (time.time(), username)
        request.session['token'] = b64
        request.session['cobbler_token'] = cobbler_token
        settings = remote.get_settings()
        exipry_time = settings['auth_token_expiration']
        request.session.set_expiry(exipry_time)
        #启用单点登陆功能
        try:
            sessions = Session.objects.all()
            online = len(sessions)
            if online == 0:
                online = online + 1
            for session in sessions:
                if session.session_key == request.session.session_key:
                    continue
                else:
                    session_data = session.session_data
                    session_data_decode = base64.b64decode(session_data)
                    ds = session_data_decode.split(':',1)[1]
                    session_data_json = simplejson.loads(ds)
                    if session_data_json.has_key('quick_meta'):
                        meta_old = session_data_json['quick_meta']
                        if meta_old :
                            meta_old = simplejson.loads(meta_old)
                            if meta_old['username'] == username:
                                Session.objects.filter(session_key=session.session_key).delete()
                                login_log = Login_Log(time=now,action='登出',user=username,status='成功',ip=request.META['REMOTE_ADDR'],remark='账号在另一区域登陆')
                                login_log.save()
            user_profile = User_Profile.objects.filter(username=username)
            if user_profile:
                bg = user_profile[0].background
                topbar = user_profile[0].topbar
            else:
                bg = 'bg1'
                topbar = 'light-blue'
            meta = {"online":online,"username":username,"usermail":user.email,"menu":menu,"have_right":have_right,"notice":2,"bg":bg,"topbar":topbar,"is_admin":user.is_superuser}
            request.session['quick_meta'] = simplejson.dumps(meta)
        except Exception as e:
            login_log = Login_Log(time=now,action='登入',user=username,status='失败',ip=request.META['REMOTE_ADDR'],remark='系统异常')
            login_log.save()
            return HttpResponse(str(e))
        login_log = Login_Log(time=now,action='登入',user=username,status='成功',ip=request.META['REMOTE_ADDR'],remark='正常登陆')
        login_log.save()
        user.online='yes'
        user.save()
        if nextsite:
           return HttpResponseRedirect(nextsite)
        else:
           return HttpResponseRedirect("/quick")
    else:
        login_log = Login_Log(time=now,action='登入',user=username,status='失败',ip=request.META['REMOTE_ADDR'],remark='令牌无效')
        login_log.save()
        return login(request,nextsite,message="登录失败，请重试")







