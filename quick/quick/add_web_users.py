#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponse
from datetime import datetime
import hashlib
import uuid
from quick.models import Users,User_Profile,System,Rights
def add_web_users(request):
    try:
        password = u"root"
        password_md5 = hashlib.md5(password.encode(encoding='UTF-8')).hexdigest()
        root = Users(employee_id='350001',username='root',password=password_md5,email='root@163.com',name='administrator',telephone='12345678910',sex=u'男',photo='none',token=str(uuid.uuid4()).replace('-',''),token_expire_time='2999-10-10 10:10:01',reset_token=str(uuid.uuid4()).replace('-',''),reset_token_expire_time='2999-10-10 10:10:01',is_superuser='yes',is_active='yes',registry_time=datetime.now())
        root.save()
        user = Users.objects.filter(username='root')
        if user:
            user = user[0]
            user_profile = User_Profile(user_id=user.id,username=user.username)
            user_profile.save()
            system = System()
            system.save()
            right = Rights(name='host_single',menu1_title='主机管理',menu1_icon='fa fa-desktop',menu2_title='单机管理',menu2_url='/quick/host/single/list',desc='单机管理')
            right.save()
    except Exception, e:
        return HttpResponse(str(e))
    else:
        return HttpResponse('已成功添加web用户账号(root:root)')


