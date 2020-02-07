#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.template import RequestContext
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render_to_response

@csrf_protect
def login(request, next=None, message=None, expired=False):
    if expired and not message:
        message = ""
    return render_to_response('login.tmpl', RequestContext(request,{'next':next,'message':message}))

