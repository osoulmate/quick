#!/usr/bin/env python
# -*- coding:utf-8 -*-
from datetime import datetime
import time
import base64
import xmlrpclib
import cobbler.utils as utils
from quick.models import Users

remote = None

def test_user_authenticated(request):
    global remote
    url_cobbler_api = None
    if url_cobbler_api is None:
        url_cobbler_api = utils.local_get_cobbler_api_url()
    if request.session.has_key('cobbler_token') and request.session['cobbler_token'] != '':
        try:
            remote = xmlrpclib.Server(url_cobbler_api, allow_none=True)
            settings = remote.get_settings()
            exipry_time = settings['auth_token_expiration']
            if remote.token_check(request.session['cobbler_token']):
                if request.session.has_key('token') and request.session['token'] != '':
                    b64 = request.session['token']
                    (cobbler_tokentime, cobbler_token_user) = request.session[b64]
                    #当`auth_token_expiration`参数值修改后比修改前小时，修改后会话过期时间立即生效，否则需要重新登陆生效
                    if (cobbler_tokentime + exipry_time < time.time()):
                        return False
                    request.session[b64] = (time.time(),cobbler_token_user)
                    if request.session.has_key('username') and request.session['username'] == cobbler_token_user:
                        request_url = request.path
                        current_menu = request.session['%s_menu'%request.session['username']]
                        for menu in current_menu:
                            for sub in menu['children']:
                                sub['menustate'] = 'inactive'
                            menu['menustate'] = 'inactive'
                        for menu in current_menu:
                            for sub in menu['children']:
                                if sub['url'] == request_url:
                                    sub['menustate'] = 'active'
                                    menu['menustate'] = 'active'
                                if menu['menustate'] == 'active':
                                    break
                        request.session['%s_menu'%request.session['username']] = current_menu
                        return True
                else:
                    return False
            else:
                return False
        except:
            # just let it fall through to the 'return False' below
            pass
    return False






