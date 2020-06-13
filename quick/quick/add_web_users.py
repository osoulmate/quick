#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponse
from datetime import datetime
import hashlib
import uuid
from quick.models import Users,User_Profile,System,Rights,Group_Right,Groups

def add_web_users(request):
    try:
        password = u"root"
        password_md5 = hashlib.md5(password.encode(encoding='UTF-8')).hexdigest()
        root = Users(employee_id='000001',username='root',password=password_md5,email='root@163.com',name='administrator',telephone='12345678910',sex=u'男',photo='none',token=str(uuid.uuid4()).replace('-',''),token_expire_time='2999-10-10 10:10:01',reset_token=str(uuid.uuid4()).replace('-',''),reset_token_expire_time='2999-10-10 10:10:01',is_superuser='yes',is_active='yes',registry_time=datetime.now())
        root.save()
        user = Users.objects.filter(username='root')
        if user:
            user = user[0]
            user_profile = User_Profile(user_id=user.id,username=user.username)
            user_profile.save()
            system = System()
            system.save()
            # 初始化权限
            querysetlist = [
            {"name":"host_single","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"单机管理","menu2_url":"host/single/list","desc":"menu"},
            {"name":"host_batch","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"批处理","menu2_url":"host/batch/list","desc":"menu"},
            {"name":"host_group","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"主机组","menu2_url":"host/group/list","desc":"menu"},
            {"name":"host_script","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"脚本","menu2_url":"host/script/list","desc":"menu"},

            {"name":"create_task","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"创建任务","menu2_url":"install/edit","desc":"menu"},
            {"name":"task_list","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"任务列表","menu2_url":"install/resume/list","desc":"menu"},
            {"name":"task_detail","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"任务详情","menu2_url":"install/detail/list","desc":"menu"},
            {"name":"task_history","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"历史任务","menu2_url":"install/history/list","desc":"menu"},

            {"name":"app_view","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"业务视图","menu2_url":"asset/app/list","desc":"menu"},
            {"name":"hardware_view","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"硬件视图","menu2_url":"asset/hardware/list","desc":"menu"},
            {"name":"union_view","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"运维视图","menu2_url":"asset/union/list","desc":"menu"},

            {"name":"presence_host","menu1_title":"虚拟化","menu1_icon":"fa-sitemap","menu2_title":"宿主机","menu2_url":"presence/list","desc":"menu"},
            {"name":"virtual_host","menu1_title":"虚拟化","menu1_icon":"fa-sitemap","menu2_title":"虚拟机","menu2_url":"virtual/list","desc":"menu"},

            {"name":"ip_pool","menu1_title":"资源池","menu1_icon":"fa-globe","menu2_title":"地址池","menu2_url":"ippool/list","desc":"menu"},
            {"name":"storage_pool","menu1_title":"资源池","menu1_icon":"fa-globe","menu2_title":"存储池","menu2_url":"storage/list","desc":"menu"},

            {"name":"import_list","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"导入ISO","menu2_url":"import/prompt","desc":"menu"},
            {"name":"distros_list","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"Distros","menu2_url":"distro/list","desc":"menu"},
            {"name":"profiles_list","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"Profiles","menu2_url":"profile/list","desc":"menu"},
            {"name":"systems_list","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"Systems","menu2_url":"system/list","desc":"menu"},
            {"name":"kickstarts_list","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"Kickstarts","menu2_url":"ksfile/list","desc":"menu"},
            {"name":"snippets_list","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"Snippets","menu2_url":"snippet/list","desc":"menu"},

            {"name":"para_config","menu1_title":"系统设置","menu1_icon":"fa-bars","menu2_title":"参数配置","menu2_url":"setting/list","desc":"menu"},
            {"name":"check_config","menu1_title":"系统设置","menu1_icon":"fa-bars","menu2_title":"配置检查","menu2_url":"check","desc":"menu"},
            {"name":"update_config","menu1_title":"系统设置","menu1_icon":"fa-bars","menu2_title":"更新配置","menu2_url":"sync","desc":"menu"},

            {"name":"users_list","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"用户列表","menu2_url":"user/user/list","desc":"menu"},
            {"name":"roles_list","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"角色列表","menu2_url":"user/role/list","desc":"menu"},
            {"name":"rights_list","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"权限列表","menu2_url":"user/right/list","desc":"menu"},

            {"name":"login_log","menu1_title":"日志","menu1_icon":"fa-bullseye","menu2_title":"登录日志","menu2_url":"log/login","desc":"menu"},
            {"name":"manual_log","menu1_title":"日志","menu1_icon":"fa-bullseye","menu2_title":"操作日志","menu2_url":"log/manual","desc":"menu"},
            {"name":"asset_log","menu1_title":"日志","menu1_icon":"fa-bullseye","menu2_title":"资产日志","menu2_url":"log/asset","desc":"menu"},
            {"name":"envent_log","menu1_title":"日志","menu1_icon":"fa-bullseye","menu2_title":"Events","menu2_url":"events","desc":"menu"},

            {"name":"host_group_edit","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"编辑主机组","menu2_url":"host/group/edit/.+","desc":"修改"},
            {"name":"host_group_new","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"新建主机组","menu2_url":"host/group/edit","desc":"新建"},
            {"name":"host_group_save","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"保存主机组","menu2_url":"host/group/save","desc":"保存"},
            {"name":"host_group_del","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"删除主机组","menu2_url":"host/group/delete/.+","desc":"删除"},
            {"name":"host_group_batch_action","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"批处理主机组","menu2_url":"host/group/multi/.+/.+","desc":"批处理"},

            {"name":"host_script_edit","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"编辑脚本","menu2_url":"host/script/edit/.+","desc":"修改"},
            {"name":"host_script_new","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"新建脚本","menu2_url":"host/script/edit","desc":"新建"},
            {"name":"host_script_save","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"保存脚本","menu2_url":"host/script/save","desc":"保存"},
            {"name":"host_script_del","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"删除脚本","menu2_url":"host/script/delete/.+","desc":"删除"},
            {"name":"host_script_batch_action","menu1_title":"主机管理","menu1_icon":"fa-desktop","menu2_title":"批处理脚本","menu2_url":"host/script/multi/.+/.+","desc":"批处理"},

            {"name":"edit_task","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"编辑任务","menu2_url":"install/edit/.+","desc":"修改"},
            {"name":"save_task","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"保存任务","menu2_url":"install/save","desc":"保存"},
            {"name":"notice_task","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"任务通知","menu2_url":"install/notice/.+","desc":"通知"},
            {"name":"execute_task","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"执行任务","menu2_url":"install/execute/.+","desc":"执行"},
            {"name":"del_task","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"删除任务","menu2_url":"install/\w+/delete/.+","desc":"删除"},
            {"name":"batch_action_task","menu1_title":"系统安装","menu1_icon":"fa-layer-group","menu2_title":"任务批处理","menu2_url":"install/\w+/multi/.+/.+","desc":"批处理"},

            {"name":"app_view_edit","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"编辑业务资产","menu2_url":"asset/app/edit/.+","desc":"修改"},
            {"name":"app_view_edit_batch","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"批量编辑业务资产","menu2_url":"asset/app/edit\?action=batch","desc":"批量修改"},
            {"name":"app_view_new","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"新建业务资产","menu2_url":"asset/app/edit","desc":"新建"},
            {"name":"app_view_save","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"保存业务资产","menu2_url":"asset/app/save","desc":"保存"},
            {"name":"app_view_del","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"删除业务资产","menu2_url":"asset/app/delete/.+","desc":"删除"},
            {"name":"app_view_batch_action","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"业务资产批处理","menu2_url":"asset/app/multi/.+/.+","desc":"批处理"},

            {"name":"hardware_view_edit","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"编辑硬件资产","menu2_url":"asset/hardware/edit/.+","desc":"修改"},
            {"name":"hardware_view_edit_batch","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"批量编辑硬件资产","menu2_url":"asset/hardware/edit\?action=batch+","desc":"批量修改"},
            {"name":"hardware_view_new","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"新建硬件资产","menu2_url":"asset/hardware/edit","desc":"新建"},
            {"name":"hardware_view_save","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"保存硬件资产","menu2_url":"asset/hardware/save","desc":"保存"},
            {"name":"hardware_view_delete","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"删除硬件资产","menu2_url":"asset/hardware/delete/.+","desc":"删除"},
            {"name":"hardware_view_batch_action","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"硬件资产批处理","menu2_url":"asset/hardware/multi/.+/.+","desc":"批处理"},

            {"name":"asset_import","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"资产导入","menu2_url":"asset/\w+/import","desc":"导入"},
            {"name":"asset_export","menu1_title":"资产管理","menu1_icon":"fa-database","menu2_title":"资产导出","menu2_url":"asset/\w+/export","desc":"导出"},

            {"name":"import_run","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"执行导入ISO","menu2_url":"import/run","desc":"执行"},

            {"name":"distros_edit","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"修改Distros","menu2_url":"distro/edit/.+","desc":"修改"},
            {"name":"distros_new","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"新建Distros","menu2_url":"distro/edit","desc":"新建"},
            {"name":"distros_save","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"保存Distros","menu2_url":"distro/save","desc":"保存"},

            {"name":"profiles_edit","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"修改Profiles","menu2_url":"profile/edit/.+","desc":"修改"},
            {"name":"profiles_new","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"新建Profiles","menu2_url":"profile/edit","desc":"新建"},
            {"name":"profiles_save","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"保存Profiles","menu2_url":"profile/save","desc":"保存"},

            {"name":"systems_edit","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"修改Systems","menu2_url":"system/edit/.+","desc":"修改"},
            {"name":"systems_new","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"新建Systems","menu2_url":"system/edit","desc":"新建"},
            {"name":"systems_save","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"保存Systems","menu2_url":"system/save","desc":"保存"},

            {"name":"kickstarts_edit","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"修改Kickstarts","menu2_url":"ksfile/edit/file:.*","desc":"修改"},
            {"name":"kickstarts_new","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"新建Kickstarts","menu2_url":"ksfile/edit","desc":"新建"},
            {"name":"kickstarts_save","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"保存Kickstarts","menu2_url":"ksfile/save:","desc":"保存"},

            {"name":"snippets_edit","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"修改Snippets","menu2_url":"snippet/edit/file:.*","desc":"修改"},
            {"name":"snippets_new","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"新建Snippets","menu2_url":"snippet/edit","desc":"新建"},
            {"name":"snippets_save","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"保存Snippets","menu2_url":"snippet/save","desc":"保存"},

            {"name":"general_del","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"通用删除功能","menu2_url":"\w+/delete/.+","desc":"删除"},
            {"name":"general_batch_action","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"通用批处理功能","menu2_url":"\w+/multi/.+/.+","desc":"批处理"},
            {"name":"general_rename","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"通用重命名功能","menu2_url":"\w+/rename/.+/.+","desc":"重命名"},
            {"name":"general_copy","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"通用复制功能","menu2_url":"\w+/copy/.+/.+","desc":"复制"},

            {"name":"general_modifylist_1","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"通用1","menu2_url":"\w+/modifylist/[!\w]+/.+","desc":"排序|翻页"},
            {"name":"general_modifylist_2","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"通用2","menu2_url":"\w+/\w+/modifylist/[!\w]+/.+","desc":"排序|翻页"},
            {"name":"install_modifylist","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"通用3","menu2_url":"install/\w+/modifylist/[!\w]+/.+","desc":"排序|翻页"},

            {"name":"general_ajax","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"ajax","menu2_url":"ajax","desc":"ajax"},

            {"name":"general_eventlog","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"eventlog","menu2_url":"eventlog/.+","desc":"eventlog"},
            {"name":"general_iplist","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"iplist","menu2_url":"iplist","desc":"iplist"},
            {"name":"general_task_created","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"task_created","menu2_url":"task_created","desc":"task_created"},
            {"name":"general_reposync","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"reposync","menu2_url":"reposync","desc":"reposync"},
            {"name":"general_replicate","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"replicate","menu2_url":"replicate","desc":"replicate"},
            {"name":"general_hardlink","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"hardlink","menu2_url":"hardlink","desc":"hardlink"},
            {"name":"general_random_mac","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"random_mac","menu2_url":"utils/random_mac","desc":"random_mac"},
            {"name":"general_random_mac_type","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"random_mac_type","menu2_url":"utils/random_mac/virttype/.+","desc":"random_mac_type"},
            {"name":"index","menu1_title":"配置管理","menu1_icon":"fa-paint-roller","menu2_title":"index","menu2_url":"","desc":"index"},

            {"name":"para_config_edit","menu1_title":"系统设置","menu1_icon":"fa-bars","menu2_title":"编辑参数配置","menu2_url":"setting/edit/.+","desc":"编辑"},
            {"name":"para_config_save","menu1_title":"系统设置","menu1_icon":"fa-bars","menu2_title":"保存参数配置","menu2_url":"setting/save","desc":"保存"},

            {"name":"user_chg_pwd","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"用户密码修改","menu2_url":"user/changepwd","desc":"修改密码"},
            {"name":"user_info","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"用户个人资料","menu2_url":"user/myinfo","desc":"个人资料"},
            {"name":"my_save","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"保存修改","menu2_url":"user/save","desc":"保存"},

            {"name":"users_func","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"用户功能","menu2_url":"user/\w+/.+/.+","desc":"删除|启用|禁用"},
            {"name":"users_batch_action","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"用户批处理","menu2_url":"user/\w+/multi/.+/.+","desc":"批处理"},

            {"name":"users_edit","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"编辑用户","menu2_url":"user/user/edit/.+","desc":"编辑"},
            {"name":"users_new","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"新建用户","menu2_url":"user/user/edit","desc":"新建"},
            {"name":"users_save","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"保存用户","menu2_url":"user/user/save","desc":"保存"},

            {"name":"roles_edit","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"编辑角色","menu2_url":"user/role/edit/.+","desc":"编辑"},
            {"name":"roles_new","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"新建角色","menu2_url":"user/role/edit","desc":"新建"},
            {"name":"roles_save","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"保存角色","menu2_url":"user/role/save","desc":"保存"},

            {"name":"rights_edit","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"编辑权限","menu2_url":"user/right/edit/.+","desc":"编辑"},
            {"name":"rights_new","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"新建权限","menu2_url":"user/right/edit","desc":"新建"},
            {"name":"rights_save","menu1_title":"用户管理","menu1_icon":"fa-user","menu2_title":"保存权限","menu2_url":"user/right/save","desc":"保存"}
            ]
            queryset = []
            for query in querysetlist:
                queryset.append(Rights(**query))
            Rights.objects.bulk_create(queryset)
             # 初始化角色
            role_query_set_list = [
            {"name":"管理员组","desc":"拥有最高权限"},
            {"name":"运维组","desc":"拥有运维相关权限"},
            {"name":"应用资产组","desc":"拥有应用资产管理权限"},
            {"name":"硬件资产组","desc":"拥有硬件资产管理权限"},
            {"name":"系统安装组","desc":"拥有系统安装相关权限"},
            {"name":"审计组","desc":"拥有日志管理权限"}
            ]

            queryset = []
            for query in role_query_set_list:
                queryset.append(Groups(**query))
            Groups.objects.bulk_create(queryset)

            groups = Groups.objects.all()
            rights = Rights.objects.all()
            for group in groups:
                have_rights = []
                if group.name == '运维组':
                    have_rights = ["general_modifylist_1","general_modifylist_2","index","host_single","host_batch","host_group","host_script","host_group_edit","host_group_new","host_group_save","host_group_del","host_group_batch_action","host_script_edit","host_script_new","host_script_save","host_script_del","host_script_batch_action","union_view","general_ajax","user_chg_pwd","user_info","my_save"]
                elif group.name == '应用资产组':
                    have_rights = ["general_modifylist_1","general_modifylist_2","index","app_view","app_view_edit","app_view_edit_batch","app_view_new","app_view_save","app_view_del","app_view_batch_action","asset_import","asset_export","general_ajax","user_chg_pwd","user_info","my_save"]
                elif group.name == '硬件资产组':
                    have_rights = ["general_modifylist_1","general_modifylist_2","index","hardware_view","hardware_view_edit","hardware_view_edit_batch","hardware_view_new","hardware_view_save","hardware_view_delete","hardware_view_batch_action","asset_import","asset_export","general_ajax","user_chg_pwd","user_info","my_save"]
                elif group.name == '系统安装组':
                    have_rights = ["index","install_modifylist","create_task","task_list","task_detail","task_history","edit_task","save_task","notice_task","execute_task","del_task","batch_action_task","general_ajax","user_chg_pwd","user_info","my_save"]
                elif group.name == '审计组':
                    have_rights = ["general_modifylist_1","general_modifylist_2","general_eventlog","index","login_log","manual_log","asset_log","envent_log","user_chg_pwd","user_info","my_save"]
                else:
                    pass
                group_right_query = []
                for right in rights:
                    kw = {}
                    if right.name in have_rights or group.name == '管理员组':
                        kw = {"group_id":group.id,"right_id":right.id}
                        group_right_query.append(Group_Right(**kw))
                Group_Right.objects.bulk_create(group_right_query)

    except Exception, e:
        return HttpResponse(str(e))
    else:
        return HttpResponse('已成功添加web用户账号(root:root)')




