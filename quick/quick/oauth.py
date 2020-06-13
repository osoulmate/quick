#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.contrib.sessions.models import Session
from datetime import datetime
import time
import base64
import xmlrpclib
import simplejson
import cobbler.utils as cobbler_utils
import utils
from quick.models import Users,User_Profile

remote = None
logger = utils.Logger(logfile="/var/log/quick/auth.log")
def test_user_authenticated(request):
    global remote
    url_cobbler_api = None
    if url_cobbler_api is None:
        url_cobbler_api = cobbler_utils.local_get_cobbler_api_url()
    if request.session.has_key('quick_meta'):
        meta = simplejson.loads(request.session.get('quick_meta', "{}"))
    else:
        return False
    if request.session.has_key('cobbler_token') and request.session['cobbler_token'] != '':
        try:
            remote = xmlrpclib.Server(url_cobbler_api, allow_none=True)
        except:
            logger.error("用户(%s)访问URL(%s)失败,原因：[无法获取Cobbler接口]"%(meta['username'],request.path))
            return False
        else:
            settings = remote.get_settings()
            exipry_time = settings['auth_token_expiration']
            try:
                t = remote.token_check(request.session['cobbler_token'])
            except Exception,e:
                logger.error("用户(%s)访问URL(%s)异常,异常：[%s]"%(meta['username'],request.path,str(e)))
                return True
            else:
                if t:
                    if request.session.has_key('token') and request.session['token'] != '':
                        b64 = request.session['token']
                        (cobbler_tokentime, cobbler_token_user) = request.session[b64]
                        #当`auth_token_expiration`参数值修改后比修改前小时，修改后会话过期时间立即生效，否则需要重新登陆生效
                        if (cobbler_tokentime + exipry_time < time.time()):
                            logger.error("用户(%s)访问URL(%s)失败,原因：[会话超时]"%(meta['username'],request.path))
                            return False
                        request.session[b64] = (time.time(),cobbler_token_user)
                        for menu in meta['menu']:
                            for sub in menu['children']:
                                sub['menustate'] = 'inactive'
                            menu['menustate'] = 'inactive'
                        for menu in meta['menu']:
                            for sub in menu['children']:
                                if "/quick/"+sub['url'] == request.path:
                                    sub['menustate'] = 'active'
                                    menu['menustate'] = 'active'
                                if menu['menustate'] == 'active':
                                    break
                        sessions = Session.objects.all()
                        meta['online'] = len(sessions)
                        user_profile = User_Profile.objects.filter(username=meta['username'])
                        if user_profile:
                            bg = user_profile[0].background
                            topbar = user_profile[0].topbar
                        else:
                            bg = 'bg1'
                            topbar = 'light-blue'
                        meta['bg'] = bg
                        meta['topbar'] = topbar
                        request.session['quick_meta'] = simplejson.dumps(meta)
                        #logger.info("用户(%s)访问URL(%s)成功"%(meta['username'],request.path))
                        return True
                    else:
                        logger.error("用户(%s)访问URL(%s)失败,原因：[无效的会话令牌]"%(meta['username'],request.path))
                        return False
                else:
                    logger.error("用户(%s)访问URL(%s)失败,原因：[cobbler令牌已过期]"%(meta['username'],request.path))
                    return False
    else:
        logger.error("用户(%s)访问URL(%s)失败,原因：[无效的cobbler令牌]"%(meta['username'],request.path))
        return False



