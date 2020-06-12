from django.conf.urls import patterns
import login
import do_login
import do_logout
import common
import index
import views
import install
import users
import assets
import ajax
import test
import add_web_users
urlpatterns = patterns('',
    (r'^$', index.index),
    (r'^ajax$', ajax.ajax),
    (r'^events$', views.events),
    (r'^eventlog/(?P<event>.+)$', views.eventlog),
    (r'^iplist$', views.iplist),
    (r'^task_created$', views.task_created),
    (r'^sync$', views.sync),
    (r'^reposync$',views.reposync),
    (r'^replicate$',views.replicate),
    (r'^hardlink', views.hardlink),
    (r'^import/prompt$', views.import_prompt),
    (r'^import/run$', views.import_run),
    (r'^buildiso$', views.buildiso),
    (r'^check$', views.check),
    (r'^login$', login.login),
    (r'^do_login$', do_login.do_login),
    (r'^logout1$', do_logout.do_logout_timeout),
    (r'^logout$', do_logout.do_logout),
    (r'^test$', test.test),
    (r'^add_web_users$', add_web_users.add_web_users),
    (r'^utils/random_mac$', views.random_mac),
    (r'^utils/random_mac/virttype/(?P<virttype>.+)$', views.random_mac),

    (r'^(?P<what>\w+)/modifylist/(?P<pref>[!\w]+)/(?P<value>.+)$', views.modify_list),

    (r'^(?P<obj>\w+)/(?P<what>\w+)/modifylist/(?P<pref>[!\w]+)/(?P<value>.+)$', common.modify_list),
    (r'^asset/(?P<what>\w+)/list(/(?P<page>\d+))?', assets.asset_list),
    (r'^asset/(?P<what>\w+)/edit/(?P<obj_name>.+)$', assets.asset_edit, {'editmode': 'edit'}),
    (r'^asset/(?P<what>\w+)/edit$', assets.asset_edit, {'editmode': 'new'}),
    (r'^asset/(?P<what>\w+)/save$', assets.asset_save),
    (r'^asset/(?P<what>\w+)/import$', assets.asset_import),
    (r'^asset/(?P<what>\w+)/export$', assets.asset_export),
    (r'^asset/(?P<what>\w+)/delete/(?P<obj_name>.+)$', assets.asset_delete),
    (r'^asset/(?P<what>\w+)/multi/(?P<multi_mode>.+)/(?P<multi_arg>.+)$', assets.asset_domulti),

    (r'^host/(?P<what>\w+)/list(/(?P<page>\d+))?', assets.host_list),
    (r'^host/(?P<what>\w+)/edit/(?P<obj_name>.+)$', assets.host_edit, {'editmode': 'edit'}),
    (r'^host/(?P<what>\w+)/edit$', assets.host_edit, {'editmode': 'new'}),
    (r'^host/(?P<what>\w+)/save$', assets.host_save),
    (r'^host/(?P<what>\w+)/delete/(?P<obj_name>.+)$', assets.asset_delete),
    (r'^host/(?P<what>\w+)/multi/(?P<multi_mode>.+)/(?P<multi_arg>.+)$', assets.asset_domulti),

    (r'^presence/list(/(?P<page>\d+))?$', assets.presence_list),
    (r'^presence/edit$', assets.presence_edit, {'editmode':'new'}),
    (r'^presence/edit/(?P<ip>.+)$', assets.presence_edit, {'editmode':'edit'}),
    (r'^presence/save$', assets.presence_save),
    (r'^virtual/list(/(?P<page>\d+))?$', assets.virtual_list),

    (r'^log/(?P<what>\w+)(/(?P<page>\d+))?$', users.logit),
    (r'^ippool/list(/(?P<page>\d+))?$', assets.ippool_list),
    (r'^ippool/edit$', assets.ippool_edit, {'editmode':'new'}),
    (r'^ippool/edit/(?P<ip>.+)$', assets.ippool_edit, {'editmode':'edit'}),
    (r'^ippool/save$', assets.ippool_save),

    (r'^storage/list(/(?P<page>\d+))?$', assets.storage_list),
    (r'^storage/edit/(?P<ip>.+)$', assets.storage_edit, {'editmode':'edit'}),
    (r'^storage/save$', assets.storage_save),

    (r'^setting/list$', views.setting_list),
    (r'^setting/edit/(?P<setting_name>.+)$', views.setting_edit),
    (r'^setting/save$', views.setting_save),

    (r'^ksfile/list(/(?P<page>\d+))?$', views.ksfile_list),
    (r'^ksfile/edit$', views.ksfile_edit, {'editmode':'new'}),
    (r'^ksfile/edit/file:(?P<ksfile_name>.+)$', views.ksfile_edit, {'editmode':'edit'}),
    (r'^ksfile/save$', views.ksfile_save),

    (r'^snippet/list(/(?P<page>\d+))?$', views.snippet_list),
    (r'^snippet/edit$', views.snippet_edit, {'editmode':'new'}),
    (r'^snippet/edit/file:(?P<snippet_name>.+)$', views.snippet_edit, {'editmode':'edit'}),
    (r'^snippet/save$', views.snippet_save),

    (r'^install/edit$', install.task_edit, {'editmode':'new'}),
    (r'^install/edit/(?P<task_name>.+)$', install.task_edit, {'editmode':'edit'}),
    (r'^install/notice/(?P<task_name>.+)$', install.task_state),
    (r'^install/save$', install.task_save),
    (r'^install/execute/(?P<task_name>.+)$', install.task_execute),
    (r'^install/(?P<what>\w+)/delete/(?P<task_name>.+)$', install.task_delete),
    (r'^install/(?P<what>\w+)/multi/(?P<multi_mode>.+)/(?P<multi_arg>.+)$', install.task_domulti),
    #(r'^install/(?P<what>\w+)/modifylist/(?P<pref>[!\w]+)/(?P<value>.+)$', install.modify_list),
    (r'^install/(?P<what>\w+)/list(/(?P<page>\d+))?', install.tasklist),

    (r'^user/changepwd$', users.changepwd),
    (r'^user/myinfo$', users.myinfo),
    (r'^user/save$', users.my_save),
    (r'^user/(?P<what>\w+)/edit$', users.user_edit, {'editmode':'new'}),
    (r'^user/(?P<what>\w+)/edit/(?P<obj_name>.+)$', users.user_edit, {'editmode':'edit'}),
    #(r'^user/(?P<what>\w+)/modifylist/(?P<pref>[!\w]+)/(?P<value>.+)$', users.modify_list),
    (r'^user/(?P<what>\w+)/list(/(?P<page>\d+))?$', users.user_list),
    (r'^user/(?P<what>\w+)/save$', users.user_save),
    (r'^user/(?P<what>\w+)/multi/(?P<multi_mode>.+)/(?P<multi_arg>.+)$', users.user_domulti),
    (r'^user/(?P<what>\w+)/(?P<action>.+)/(?P<name>.+)$', users.user_manual),

    (r'^(?P<what>\w+)/list(/(?P<page>\d+))?', views.genlist),
    (r'^(?P<what>\w+)/edit/(?P<obj_name>.+)$', views.generic_edit, {'editmode': 'edit'}),
    (r'^(?P<what>\w+)/edit$', views.generic_edit, {'editmode': 'new'}),
    (r'^(?P<what>\w+)/rename/(?P<obj_name>.+)/(?P<obj_newname>.+)$', views.generic_rename),
    (r'^(?P<what>\w+)/copy/(?P<obj_name>.+)/(?P<obj_newname>.+)$', views.generic_copy),
    (r'^(?P<what>\w+)/delete/(?P<obj_name>.+)$', views.generic_delete),
    (r'^(?P<what>\w+)/multi/(?P<multi_mode>.+)/(?P<multi_arg>.+)$', views.generic_domulti),
    (r'^(?P<what>\w+)/save$', views.generic_save),

)






