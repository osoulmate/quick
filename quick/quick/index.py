#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.template.loader import get_template
from django.template import RequestContext
from django.http import HttpResponse
from django.contrib.sessions.models import Session
import simplejson
import oauth
from login import login

def index(request):
    """
    主页
    """
    if not oauth.test_user_authenticated(request):
        return login(request,next="/quick")
    t = get_template('index.tmpl')
    html = t.render(RequestContext(request,{
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)



