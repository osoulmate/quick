#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.template.loader import get_template
from django.template import RequestContext
from django.http import HttpResponse
from django.contrib.sessions.models import Session
import oauth
from login import login

def index(request):
    """
    主页
    """
    if not oauth.test_user_authenticated(request):
        return login(request,next="/quick")
    sessions = Session.objects.all()
    online_user = len(sessions)
    t = get_template('index.tmpl')
    html = t.render(RequestContext(request,{
        'online_user': online_user,
        'username': request.session['username'],
        'menu' : request.session['%s_menu'%request.session['username']]
    }))
    return HttpResponse(html)


