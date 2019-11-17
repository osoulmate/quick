#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponse
from quick.models import Users
from datetime import datetime
def add_web_users(request):
    root = Users(username='root',password='root',email='root@163.com',first_name='root',last_name='root',
    last_login=datetime.now(),is_superuser='yes',is_active='enable',is_online='offline')
    root.save()
    test = Users(username='test',password='test',email='test@163.com',first_name='test',last_name='test',
    last_login=datetime.now(),is_superuser='no',is_active='enable',is_online='offline')
    test.save()
    return HttpResponse('已成功添加web用户账号(root:root,test:test)')
