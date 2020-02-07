#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponse
from quick.models import Users,App_Temp,Hardware_Temp,Ip_Sn_Temp
from datetime import datetime
def add_web_users(request):
    root = Users(username='root',password='root',email='root@163.com',name='张张',telephone='12345678910',
    last_login=datetime.now(),is_superuser='yes',is_active='enable',is_online='offline',employee_id='00001')
    root.save()
    app_temp = App_Temp(ip                =  'on'
                        ,osrelease         =  'on'
                        ,ipmi_ip           =  'on'
                        ,monitor           =  'on'
                        ,app_level_1       =  'on'
                        ,app_level_2       =  'on'
                        ,app_level_3       =  'on'
                        ,device_type       =  'on'
                        ,order_ops_user    =  'on'
                        ,ops_user          =  'on'
                        ,ops_team          =  'on'
                        ,dev_user          =  'on'
                        ,dev_team          =  'on'
                        ,app_user          =  'on'
                        ,app_dept          =  'on'
                        ,is_cdn            =  'on'
                        ,environment       =  'on'
                        ,life_cycle_status =  'on'
                        ,num_items         =  '0')
    app_temp.save()
    hd_temp = Hardware_Temp(sn                     = 'on'
    ,model                  = 'on'
    ,vendor                 = 'on'
    ,cpu_model              = 'on'
    ,cpu_core               = 'on'
    ,cpu_fre                = 'on'
    ,memory                 = 'on'
    ,net_card               = 'on'
    ,disk                   = 'on'
    ,location               = 'on'
    ,engine_room            = 'on'
    ,rack                   = 'on'
    ,u_site                 = 'on'
    ,order_maintenance      = 'on'
    ,maintenance_start_time = 'on'
    ,maintenance_end_time   = 'on'
    ,maintenance_vendor     = 'on'
    ,project_name           = 'on'
    ,project_code           = 'on'
    ,asset_tag              = 'on'
    ,uplink                 = 'on'
    ,num_items              = '0')
    hd_temp.save()
    ipsn_temp = Ip_Sn_Temp(ip= 'on',sn= 'on',num_items = '0')
    ipsn_temp.save()
    
    return HttpResponse('已成功添加web用户账号(root:root)')
    

