#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from datetime import datetime
from django.contrib.sessions.models import Session
from quick.models import Users

@require_POST
@csrf_protect
def do_logout(request):
    Session.objects.filter(session_key=request.session.session_key).delete()
    #request.session[request.session['token']] = ""
    #request.session['token'] = ""
    #request.session['cobbler_token'] = ""
    #request.session['quick_meta'] = ""
    return HttpResponseRedirect("/quick")
#========================================================================


