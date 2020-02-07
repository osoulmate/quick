#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.template.loader import get_template
from django.template import RequestContext
from django.http import HttpResponse

import oauth
from login import login

def index(request):
    """
    主页
    """
    if not oauth.test_user_authenticated(request):
        return login(request,next="/quick", expired=True)

    t = get_template('index.tmpl')

    html = t.render(RequestContext(request,{
         'version' : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
         'username': request.session['username'],
         'menu' : request.session['%s_menu'%request.session['username']]
    }))
    return HttpResponse(html)

