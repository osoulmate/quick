#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.template.loader import get_template
from django.template import RequestContext
from django.http import HttpResponse
import simplejson
import oauth
from login import login


def error_page(request,message):
    """
    This page is used to explain error messages to the user.
    """
    if not oauth.test_user_authenticated(request): 
        return login(request,expired=True)
    meta = simplejson.loads(request.session['quick_meta'])
    # FIXME: test and make sure we use this rather than throwing lots of tracebacks for
    # field errors
    t = get_template('error_page.tmpl')
    message = message.replace("<Fault 1: \"<class 'cobbler.cexceptions.CX'>:'","Remote exception: ")
    message = message.replace("'\">","")
    html = t.render(RequestContext(request,{
        'version' : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'message' : message,
        'meta' : meta
    }))
    return HttpResponse(html)


