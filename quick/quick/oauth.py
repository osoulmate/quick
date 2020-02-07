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
    remote = xmlrpclib.Server(url_cobbler_api, allow_none=True)
    # if we have a cobbler_token, get the associated username from
    # the remote server via XMLRPC. We then compare that to
    # the value stored in the session.  If everything matches up,
    # the user is considered successfully authenticated
    if request.session.has_key('cobbler_token') and request.session['cobbler_token'] != '':
        try:
            if remote.token_check(request.session['cobbler_token']):
                if request.session.has_key('token') and request.session['token'] != '':
                    b64 = request.session['token']
                    (cobbler_tokentime, cobbler_token_user) = request.session[b64]
                    timenow = time.time()
                    if (timenow > cobbler_tokentime + 3600):
                        user = Users.objects.get(username=request.session['username'])
                        user.is_online = 'offline'
                        user.save()
                        request.session[b64]=''
                        request.session['token']=''
                        request.session['username']=''
                        request.session['%s_menu'%cobbler_token_user]= ""
                        request.session['cobbler_token'] = ""
                    else:
                        request.session[b64] = (time.time(),cobbler_token_user)
                        if request.session.has_key('username') and request.session['username'] == cobbler_token_user:
                            user = Users.objects.get(username=cobbler_token_user)
                            if user.is_online == 'offline':
                                request.session[cobbler_token_user] = ""
                                request.session[b64] = ""
                                request.session['token'] = ""
                                request.session['%s_menu'%cobbler_token_user]= ""
                                request.session['cobbler_token'] = ""
                                return False
                            else:
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



