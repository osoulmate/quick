from django.conf.urls import patterns
import views
import tasks
import users
import test
import add_web_users
urlpatterns = patterns('',
    (r'^$', views.index),
    (r'^test$', test.test),
    (r'^add_web_users$', add_web_users.add_web_users),

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

    (r'^task/edit$', tasks.task_edit, {'editmode':'new'}),
    (r'^task/edit/(?P<task_name>.+)$', tasks.task_edit, {'editmode':'edit'}),
    (r'^task/notice/(?P<task_name>.+)$', tasks.task_state),
    (r'^task/save$', tasks.task_save),
    (r'^task/execute/(?P<task_name>.+)$', tasks.task_execute),
    (r'^task/delete/(?P<task_name>.+)$', tasks.task_delete),
    (r'^task/history/delete/(?P<task_name>.+)$', tasks.task_history_delete),
    (r'^task/(?P<what>\w+)/multi/(?P<multi_mode>.+)/(?P<multi_arg>.+)$', tasks.task_domulti),
    (r'^task/(?P<what>\w+)/modifylist/(?P<pref>[!\w]+)/(?P<value>.+)$', tasks.modify_list),
    (r'^task/(?P<what>\w+)(/(?P<page>\d+))?', tasks.tasklist),

    (r'^user/edit$', users.user_edit, {'editmode':'new'}),
    (r'^user/edit/(?P<user_name>.+)$', users.user_edit, {'editmode':'edit'}),
    (r'^user/list(/(?P<page>\d+))?$', users.user_list),
    (r'^user/save$', users.user_save),
    (r'^user/multi/(?P<multi_mode>.+)/(?P<multi_arg>.+)$', users.user_domulti),
    (r'^user/single/(?P<action>.+)/(?P<name>.+)$', users.user_single),
    
    (r'^(?P<what>\w+)/list(/(?P<page>\d+))?', views.genlist),
    (r'^(?P<what>\w+)/modifylist/(?P<pref>[!\w]+)/(?P<value>.+)$', views.modify_list),
    (r'^(?P<what>\w+)/edit/(?P<obj_name>.+)$', views.generic_edit, {'editmode': 'edit'}),
    (r'^(?P<what>\w+)/edit$', views.generic_edit, {'editmode': 'new'}),

    (r'^(?P<what>\w+)/rename/(?P<obj_name>.+)/(?P<obj_newname>.+)$', views.generic_rename),
    (r'^(?P<what>\w+)/copy/(?P<obj_name>.+)/(?P<obj_newname>.+)$', views.generic_copy),
    (r'^(?P<what>\w+)/delete/(?P<obj_name>.+)$', views.generic_delete),

    (r'^(?P<what>\w+)/multi/(?P<multi_mode>.+)/(?P<multi_arg>.+)$', views.generic_domulti),
    (r'^utils/random_mac$', views.random_mac),
    (r'^utils/random_mac/virttype/(?P<virttype>.+)$', views.random_mac),
    (r'^events$', views.events),
    (r'^eventlog/(?P<event>.+)$', views.eventlog),
    (r'^iplist$', views.iplist),
    (r'^task_created$', views.task_created),
    (r'^sync$', views.sync),
    (r'^reposync$',views.reposync),
    (r'^replicate$',views.replicate),
    (r'^hardlink', views.hardlink),
    (r'^(?P<what>\w+)/save$', views.generic_save),
    (r'^import/prompt$', views.import_prompt),
    (r'^import/run$', views.import_run),
    (r'^buildiso$', views.buildiso),
    (r'^check$', views.check),

    (r'^login$', views.login),
    (r'^do_login$', views.do_login),
    (r'^logout$', views.do_logout),
)


