# -*- coding: utf-8 -*-
 
from django.http import HttpResponse
 
from quick.models import Users,Groups,Rights,User_Group,Group_Right,User_Right,Detail,List

from datetime import datetime
# 数据库操作
def test(request):
    newdata=[]
    sub_states  = Sub_State_Temp.objects.all()
    for sub_state in sub_states:
        data = [sub_state.ip,sub_state.name,sub_state.start_time,sub_state.end_time,sub_state.state]
        newdata.extend(data)
    states = State_Temp.objects.all()
    for state in states:
        data1 = [state.name,state.start_time,state.end_time,state.state]
        newdata.extend(data1)
    Sub_State_Temp.objects.all().delete()
    State_Temp.objects.all().delete()
    return HttpResponse(newdata)


