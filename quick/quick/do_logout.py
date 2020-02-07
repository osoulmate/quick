#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from datetime import datetime

from quick.models import Users

@require_POST
@csrf_protect
def do_logout(request):
    user = Users.objects.get(username=request.session['username'])
    user.is_online = 'offline'
    user.last_login = datetime.now()
    user.save()
    request.session['username'] = ""
    request.session[request.session['token']] = ""
    request.session['token'] = ""
    request.session['menu']= ""
    request.session['cobbler_token'] = ""
    return HttpResponseRedirect("/quick")
#========================================================================
