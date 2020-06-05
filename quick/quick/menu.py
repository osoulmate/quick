#!/usr/bin/env python
# -*- coding:utf-8 -*-
menu = [
            {
                "menutitle":"主机管理",
                "menuicon" :"fa-desktop",
                "menustate":"inactive",
                "children":[{'title':'单机管理','url':'/quick/host/single/list','menustate':'inactive' },
                            {'title':'批处理','url':'/quick/host/batch/list'   ,'menustate':'inactive' },
                            {'title':'主机组','url':'/quick/host/group/list'   ,'menustate':'inactive' },
                            {'title':'脚本','url':'/quick/host/script/list'    ,'menustate':'inactive' }
                            ]
            },
            {
                "menutitle":"系统安装",
                "menuicon" :"fa-layer-group",
                "menustate":"inactive",
                "children":[{'title':'创建任务','url':'/quick/install/edit'        ,'menustate':'inactive'},
                            {'title':'任务列表','url':'/quick/install/resume/list' ,'menustate':'inactive'},
                            {'title':'任务详情','url':'/quick/install/detail/list' ,'menustate':'inactive'},
                            {'title':'历史任务','url':'/quick/install/history/list','menustate':'inactive'}]
            },
            {
                "menutitle":"资产管理",
                "menuicon" :"fa-database",
                "menustate":"inactive",
                "children":[{'title':'业务视图','url':'/quick/asset/app/list'     ,'menustate':'inactive'},
                            {'title':'硬件视图','url':'/quick/asset/hardware/list','menustate':'inactive'},
                            {'title':'运维视图','url':'/quick/asset/union/list'    ,'menustate':'inactive'}]
            },
            {
                "menutitle":"虚拟化",
                "menuicon" :"fa-sitemap",
                "menustate":"inactive",
                "children":[{'title':'宿主机','url':'/quick/presence/list','menustate':'inactive'},
                            {'title':'虚拟机','url':'/quick/virtual/list' ,'menustate':'inactive'}]
            },
            {
                "menutitle":"资源池",
                "menuicon" :"fa-globe",
                "menustate":"inactive",
                "children":[{'title':'地址池','url':'/quick/ippool/list','menustate':'inactive'},
                            {'title':'存储池','url':'/quick/storage/list','menustate':'inactive'}]
            },
            {
                "menutitle":"配置管理",
                "menuicon" :"fa-paint-roller",
                "menustate":"inactive",
                "children":[{'title':'导入ISO','url':'/quick/import/prompt' ,'menustate':'inactive' },
                            {'title':'Distros','url':'/quick/distro/list'  ,'menustate':'inactive' },
                            {'title':'Profiles','url':'/quick/profile/list','menustate':'inactive'},
                            {'title':'Systems','url':'/quick/system/list'  ,'menustate':'inactive'},
                            {'title':'Kickstarts','url':'/quick/ksfile/list','menustate':'inactive'},
                            {'title':'Snippets','url':'/quick/snippet/list' ,'menustate':'inactive'}]
            },
            {
                "menutitle":"系统设置",
                "menuicon" :"fa-bars",
                "menustate":"inactive",
                "children":[{'title':'参数配置','url':'/quick/setting/list','menustate':'inactive'},
                            {'title':'配置检查','url':'/quick/check'       ,'menustate':'inactive'},
                            {'title':'更新配置','url':"javascript:menuaction('/quick/sync');",'menustate':'inactive'}]
            },
            {
                "menutitle":"用户管理",
                "menuicon" :"fa-user",
                "menustate":"inactive",
                "children":[{'title':'用户列表','url':'/quick/user/user/list/' ,'menustate':'inactive'},
                            {'title':'角色列表','url':'/quick/user/role/list/' ,'menustate':'inactive'},
                            {'title':'权限列表','url':'/quick/user/right/list/','menustate':'inactive'}]
            },
            {
                "menutitle":"日志",
                "menuicon" :"fa-bullseye",
                "menustate":"inactive",
                "children":[{'title':'登录日志','url':'/quick/log/login' ,'menustate':'inactive'},
                            {'title':'操作日志','url':'/quick/log/manual','menustate':'inactive'},
                            {'title':'资产日志','url':'/quick/log/asset','menustate':'inactive'},
                            {'title':'Events','url':'/quick/events','menustate':'inactive'}]
            }
]



