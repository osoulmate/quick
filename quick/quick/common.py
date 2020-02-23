#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.http import HttpResponseRedirect
import simplejson
import oauth
from login import login
from error_page import error_page
# ======================================================================
def modify_list(request, obj, what, pref, value=None):
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/%s/%s/list"%(obj,what), expired=True)

    if pref == "sort":

        old_sort = request.session.get("%s_sort_field" % what,"")
        if old_sort.startswith("!"):
            old_sort = old_sort[1:]
            old_revsort = True
        else:
            old_revsort = False

        if old_sort == value and not old_revsort:
            value = "!" + value
        request.session["%s_sort_field" % what] = value
        request.session["%s_page" % what] = 1

    elif pref == "limit":
        # 每页显示的条目数
        request.session["%s_limit" % what] = int(value)
        request.session["%s_page" % what] = 1

    elif pref == "page":
        # 当前页面数字
        request.session["%s_page" % what] = int(value)

    elif pref in ("addfilter","removefilter"):
        # filters limit what we show in the lists
        # they are stored in json format for marshalling
        filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))
        if pref == "addfilter":
            (field_name, field_value) = value.split(":", 1)
            # add this filter
            filters[field_name] = field_value
        else:
            # remove this filter, if it exists
            if filters.has_key(value):
                del filters[value]
        # save session variable
        request.session["%s_filters" % what] = simplejson.dumps(filters)
        # since we changed what is viewed, reset the page
        request.session["%s_page" % what] = 1

    else:
        return error_page(request, "无效请求")
    if what in ['login','manual','asset'] and obj == 'log':
        return HttpResponseRedirect("/quick/%s/%s"%(obj,what))
    # redirect to the list page
    return HttpResponseRedirect("/quick/%s/%s/list" % (obj,what))



