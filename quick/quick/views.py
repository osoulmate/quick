#!/usr/bin/env python
# -*- coding:utf-8 -*-
from django.template.loader import get_template
from django.template import RequestContext
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
import simplejson
import string
import time
import ipaddress
import cobbler.item_distro    as item_distro
import cobbler.item_profile   as item_profile
import cobbler.item_system    as item_system
import cobbler.item_repo      as item_repo
import cobbler.item_image     as item_image
import cobbler.item_mgmtclass as item_mgmtclass
import cobbler.item_package   as item_package
import cobbler.item_file      as item_file
import cobbler.settings       as item_settings
import cobbler.field_info     as field_info
import cobbler.utils          as utils

import oauth
from error_page import error_page
from login import login
#========================================================================

def task_created(request):
    """
    Let's the user know what to expect for event updates.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/task_created", expired=True)
    t = get_template("task_created.tmpl")
    html = t.render(RequestContext(request,{
        'version'  : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

#==================================================================================

def get_fields(what, is_subobject, seed_item=None):

    """
    Helper function.  Retrieves the field table from the cobbler objects
    and formats it in a way to make it useful for Django templating.
    The field structure indicates what fields to display and what the default
    values are, etc.
    """

    if what == "distro":
        field_data = item_distro.FIELDS
    if what == "profile":
        field_data = item_profile.FIELDS
    if what == "system":
        field_data = item_system.FIELDS
    if what == "repo":
        field_data = item_repo.FIELDS
    if what == "image":
        field_data =  item_image.FIELDS
    if what == "mgmtclass":
        field_data = item_mgmtclass.FIELDS
    if what == "package":
        field_data = item_package.FIELDS
    if what == "file":
        field_data = item_file.FIELDS
    if what == "setting":
        field_data = item_settings.FIELDS

    settings = oauth.remote.get_settings()

    fields = []
    for row in field_data:
        elem = {
            "name"                    : row[0],
            "dname"                   : row[0].replace("*",""),
            "value"                   : "?",
            "caption"                 : row[3],
            "editable"                : row[4],
            "tooltip"                 : row[5],
            "choices"                 : row[6],
            "css_class"               : "generic",
            "html_element"            : "generic",
        }

        if not elem["editable"]:
            continue

        if seed_item is not None:
            if what == "setting":
                elem["value"] = seed_item[row[0]]
            elif row[0].startswith("*"):
                # system interfaces are loaded by javascript, not this
                elem["value"]             = ""
                elem["name"]              = row[0].replace("*","")
            elif row[0].find("widget") == -1:
                elem["value"]             = seed_item[row[0]]
        elif is_subobject:
            elem["value"]             = row[2]
        else:
            elem["value"]             = row[1]

        if elem["value"] is None:
            elem["value"] = ""

        # we'll process this for display but still need to present the original to some
        # template logic
        elem["value_raw"]             = elem["value"]

        if isinstance(elem["value"],basestring) and elem["value"].startswith("SETTINGS:"):
            key = elem["value"].replace("SETTINGS:","",1)
            elem["value"] = settings[key]

        # flatten hashes of all types, they can only be edited as text
        # as we have no HTML hash widget (yet)
        if type(elem["value"]) == type({}):
            if elem["name"] == "mgmt_parameters":
                #Render dictionary as YAML for Management Parameters field
                tokens = []
                for (x,y) in elem["value"].items():
                    if y is not None:
                        tokens.append("%s: %s" % (x,y))
                    else:
                        tokens.append("%s: " % x)
                elem["value"] = "{ %s }" % ", ".join(tokens)
            else:
                tokens = []
                for (x,y) in elem["value"].items():
                    if isinstance(y,basestring) and y.strip() != "~":
                        y = y.replace(" ","\\ ")
                        tokens.append("%s=%s" % (x,y))
                    elif isinstance(y,list):
                        for l in y:
                            l = l.replace(" ","\\ ")
                            tokens.append("%s=%s" % (x,l))
                    elif y != None:
                        tokens.append("%s" % x)
                elem["value"] = " ".join(tokens)
        name = row[0]
        if name.find("_widget") != -1:
            elem["html_element"] = "widget"
        elif name in field_info.USES_SELECT:
            elem["html_element"] = "select"
        elif name in field_info.USES_MULTI_SELECT:
            elem["html_element"] = "multiselect"
        elif name in field_info.USES_RADIO:
            elem["html_element"] = "radio"
        elif name in field_info.USES_CHECKBOX:
            elem["html_element"] = "checkbox"
        elif name in field_info.USES_TEXTAREA:
            elem["html_element"] = "textarea"
        else:
            elem["html_element"] = "text"

        elem["block_section"] = field_info.BLOCK_MAPPINGS.get(name, "General")

        # flatten lists for those that aren't using select boxes
        if type(elem["value"]) == type([]):
            if elem["html_element"] != "select":
                elem["value"] = string.join(elem["value"], sep=" ")

        # FIXME: need to handle interfaces special, they are prefixed with "*"

        fields.append(elem)

    return fields

#==================================================================================

def __tweak_field(fields,field_name,attribute,value):
    """
    Helper function to insert extra data into the field list.
    """
    # FIXME: eliminate this function.
    for x in fields:
        if x["name"] == field_name:
            x[attribute] = value

#==================================================================================


def __format_columns(column_names,sort_field):
    """
    Format items retrieved from XMLRPC for rendering by the generic_edit template
    """
    dataset = []

    # Default is sorting on name
    if sort_field is not None:
        sort_name = sort_field
    else:
        sort_name = "name"

    if sort_name.startswith("!"):
        sort_name = sort_name[1:]
        sort_order = "desc"
    else:
        sort_order = "asc"

    for fieldname in column_names:
        fieldorder = "none"
        if fieldname == sort_name:
            fieldorder = sort_order
        dataset.append([fieldname,fieldorder])
    return dataset


#==================================================================================

def __format_items(items, column_names):
    """
    Format items retrieved from XMLRPC for rendering by the generic_edit template
    """
    dataset = []
    for itemhash in items:
        row = []
        for fieldname in column_names:
            if fieldname == "name":
                html_element = "name"
            elif fieldname in [ "system", "repo", "distro", "profile", "image", "mgmtclass", "package", "file" ]:
                html_element = "editlink"
            elif fieldname in field_info.USES_CHECKBOX:
                html_element = "checkbox"
            else:
                html_element = "text"
            row.append([fieldname,itemhash[fieldname],html_element])
        dataset.append(row)
    return dataset

#==================================================================================

def genlist(request, what, page=None):
    """
    Lists all object types, complete with links to actions
    on those objects.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/%s/list" % what, expired=True)

    # get details from the session
    if page == None:
        page = int(request.session.get("%s_page" % what, 1))
    limit = int(request.session.get("%s_limit" % what, 50))
    sort_field = request.session.get("%s_sort_field" % what, "name")
    filters = simplejson.loads(request.session.get("%s_filters" % what, "{}"))
    pageditems = oauth.remote.find_items_paged(what,utils.strip_none(filters),sort_field,page,limit)

    # what columns to show for each page?
    # we also setup the batch actions here since they're dependent
    # on what we're looking at

    # everythng gets batch delete
    batchactions = [
        ["Delete","delete","delete"],
    ]

    if what == "distro":
       columns = [ "name" ]
       batchactions += [
           ["Build ISO","buildiso","enable"],
       ]
    if what == "profile":
       columns = [ "name", "distro" ]
       batchactions += [
           ["Build ISO","buildiso","enable"],
       ]
    if what == "system":
       # FIXME: also list network, once working
       columns = [ "name", "profile", "status", "netboot_enabled" ]
       batchactions += [
           ["Power on","power","on"],
           ["Power off","power","off"],
           ["Reboot","power","reboot"],
           ["Change profile","profile",""],
           ["Netboot enable","netboot","enable"],
           ["Netboot disable","netboot","disable"],
           ["Build ISO","buildiso","enable"],
       ]
    if what == "repo":
       columns = [ "name", "mirror" ]
       batchactions += [
           ["Reposync","reposync","go"],
       ]
    if what == "image":
       columns = [ "name", "file" ]
    if what == "network":
       columns = [ "name" ]
    if what == "mgmtclass":
        columns = [ "name" ]
    if what == "package":
        columns = [ "name", "installer" ]
    if what == "file":
        columns = [ "name" ]

    # render the list
    t = get_template('generic_list.tmpl')
    html = t.render(RequestContext(request,{
        'what'           : what,
        'columns'        : __format_columns(columns,sort_field),
        'items'          : __format_items(pageditems["items"],columns),
        'pageinfo'       : pageditems["pageinfo"],
        'filters'        : filters,
        'version'        : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'limit'          : limit,
        'batchactions'   : batchactions,
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

@require_POST
@csrf_protect
def modify_list(request, what, pref, value=None):
    """
    This function is used in the generic list view
    to modify the page/column sort/number of items
    shown per page, and also modify the filters.

    This function modifies the session object to
    store these preferences persistently.
    """
    if not oauth.test_user_authenticated(request): 
        return login(request, next="/quick/%s/modifylist/%s/%s" % (what,pref,str(value)), expired=True)

    # what preference are we tweaking?

    if pref == "sort":

        # FIXME: this isn't exposed in the UI.

        # sorting list on columns
        old_sort = request.session.get("%s_sort_field" % what,"name")
        if old_sort.startswith("!"):
            old_sort = old_sort[1:]
            old_revsort = True
        else:
            old_revsort = False
        # User clicked on the column already sorted on,
        # so reverse the sorting list
        if old_sort == value and not old_revsort:
            value = "!" + value
        request.session["%s_sort_field" % what] = value
        request.session["%s_page" % what] = 1

    elif pref == "limit":
        # number of items to show per page
        request.session["%s_limit" % what] = int(value)
        request.session["%s_page" % what] = 1

    elif pref == "page":
        # what page are we currently on
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
        return error_page(request, "Invalid preference change request")

    # redirect to the list page
    return HttpResponseRedirect("/quick/%s/list" % what)

# ======================================================================

@require_POST
@csrf_protect
def generic_rename(request, what, obj_name=None, obj_newname=None):

    """
    Renames an object.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/%s/rename/%s/%s" % (what,obj_name,obj_newname), expired=True)
 
    if obj_name == None:
        return error_page(request,"您必须为 %s 定义一个名称" % what)
    if not oauth.remote.has_item(what,obj_name):
        return error_page(request,"未知定义的 %s" % what)
    elif not oauth.remote.check_access_no_fail(request.session['cobbler_token'], "modify_%s" % what, obj_name):
        return error_page(request,"您当前没有权限重命名 %s" % what)
    else:
        obj_id = oauth.remote.get_item_handle(what, obj_name, request.session['cobbler_token'])
        oauth.remote.rename_item(what, obj_id, obj_newname, request.session['cobbler_token'])
        return HttpResponseRedirect("/quick/%s/list" % what)

# ======================================================================

@require_POST
@csrf_protect
def generic_copy(request, what, obj_name=None, obj_newname=None):
    """
    Copies an object.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/%s/copy/%s/%s" % (what,obj_name,obj_newname), expired=True)
    # FIXME: shares all but one line with rename, merge it.
    if obj_name == None:
        return error_page(request,"您必须为 %s 定义一个名称" % what)
    if not oauth.remote.has_item(what,obj_name):
        return error_page(request,"未知定义的 %s" % what)
    elif not oauth.remote.check_access_no_fail(request.session['cobbler_token'], "modify_%s" % what, obj_name):
        return error_page(request,"您当前没有权限复制 %s" % what)
    else:
        obj_id = oauth.remote.get_item_handle(what, obj_name, request.session['cobbler_token'])
        try:
            oauth.remote.copy_item(what, obj_id, obj_newname, request.session['cobbler_token'])
        except Exception,e:
            return error_page(request,"%s" % str(e))
        return HttpResponseRedirect("/quick/%s/list" % what)

# ======================================================================

@require_POST
@csrf_protect
def generic_delete(request, what, obj_name=None):
    """
    Deletes an object.
    """
    if not oauth.test_user_authenticated(request):
        return login(request, next="/quick/%s/delete/%s" % (what, obj_name), expired=True)
    # FIXME: consolidate code with above functions.
    if obj_name is None:
        return error_page(request, "您必须为 %s 指定一个名称" % what)
    if not oauth.remote.has_item(what, obj_name):
        return error_page(request, "未知定义的 %s" % what)
    elif not oauth.remote.check_access_no_fail(request.session['cobbler_token'], "remove_%s" % what, obj_name):
        return error_page(request, "您当前没有权限删除 %s" % what)
    else:
        # check whether object is to be deleted recursively
        recursive = simplejson.loads(request.POST.get("recursive", "false"))
        try:
            oauth.remote.xapi_object_edit(what, obj_name, "remove", {'name': obj_name, 'recursive': recursive}, request.session['cobbler_token'])
        except Exception, e:
            return error_page(request, str(e))
        return HttpResponseRedirect("/quick/%s/list" % what)


# ======================================================================

@require_POST
@csrf_protect
def generic_domulti(request, what, multi_mode=None, multi_arg=None):
    """
    Process operations like profile reassignment, netboot toggling, and deletion
    which occur on all items that are checked on the list page.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/%s/multi/%s/%s" % (what,multi_mode,multi_arg), expired=True)

    names = request.POST.get('names', '').strip().split()
    if names == "":
        return error_page(request, "Need to select some '%s' objects first" % what)

    if multi_mode == "delete":
        # check whether the objects are to be deleted recursively
        recursive = simplejson.loads(request.POST.get("recursive_batch", "false"))
        for obj_name in names:
            try:
                oauth.remote.xapi_object_edit(what, obj_name, "remove", {'name': obj_name, 'recursive': recursive}, request.session['cobbler_token'])
            except Exception, e:
                return error_page(request, str(e))

    elif what == "system" and multi_mode == "netboot":
        netboot_enabled = multi_arg # values: enable or disable
        if netboot_enabled is None:
            return error_page(request,"Cannot modify systems without specifying netboot_enabled")
        if netboot_enabled == "enable":
            netboot_enabled = True
        elif netboot_enabled == "disable":
            netboot_enabled = False
        else:
            return error_page(request,"Invalid netboot option, expect enable or disable")
        for obj_name in names:
            obj_id = oauth.remote.get_system_handle(obj_name, request.session['cobbler_token'])
            oauth.remote.modify_system(obj_id, "netboot_enabled", netboot_enabled, request.session['cobbler_token'])
            oauth.remote.save_system(obj_id, request.session['cobbler_token'], "edit")

    elif what == "system" and multi_mode == "profile":
        profile = multi_arg
        if profile is None:
            return error_page(request,"Cannot modify systems without specifying profile")
        for obj_name in names:
            obj_id = oauth.remote.get_system_handle(obj_name, request.session['cobbler_token'])
            oauth.remote.modify_system(obj_id, "profile", profile, request.session['cobbler_token'])
            oauth.remote.save_system(obj_id, request.session['cobbler_token'], "edit")

    elif what == "system" and multi_mode == "power":
        # FIXME: power should not loop, but send the list of all systems in one set.
        power = multi_arg
        if power is None:
            return error_page(request,"Cannot modify systems without specifying power option")
        options = { "systems" : names, "power" : power }
        oauth.remote.background_power_system(options, request.session['cobbler_token'])

    elif what == "system" and multi_mode == "buildiso":
        options = { "systems" : names, "profiles" : [] }
        oauth.remote.background_buildiso(options, request.session['cobbler_token'])

    elif what == "profile" and multi_mode == "buildiso":
        options = { "profiles" : names, "systems" : [] }
        oauth.remote.background_buildiso(options, request.session['cobbler_token'])

    elif what == "distro" and multi_mode == "buildiso":
        if len(names) > 1:
            return error_page(request,"You can only select one distro at a time to build an ISO for")
        options = { "standalone" : True, "distro": str(names[0]) }
        oauth.remote.background_buildiso(options, request.session['cobbler_token'])

    elif what == "repo" and multi_mode == "reposync":
        options = {"repos": names, "tries": 3}
        oauth.remote.background_reposync(options, request.session['cobbler_token'])

    else:
        return error_page(request,"Unknown batch operation on %ss: %s" % (what,str(multi_mode)))

    # FIXME: "operation complete" would make a lot more sense here than a redirect
    return HttpResponseRedirect("/quick/%s/list"%what)

# ======================================================================

def import_prompt(request):
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/import/prompt", expired=True)
    t = get_template('import.tmpl')
    html = t.render(RequestContext(request,{
        'version'  : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

# ======================================================================

def check(request):
    """
    Shows a page with the results of 'cobbler check'
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/check", expired=True)
    results = oauth.remote.check(request.session['cobbler_token'])
    t = get_template('check.tmpl')
    html = t.render(RequestContext(request,{
        'version': oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'results'  : results,
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

# ======================================================================

@require_POST
@csrf_protect
def buildiso(request):
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/buildiso", expired=True)
    oauth.remote.background_buildiso({},request.session['cobbler_token'])
    return HttpResponseRedirect('/quick/task_created')

# ======================================================================

@require_POST
@csrf_protect
def import_run(request):
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/import/prompt", expired=True)
    options = {
        "name"  : request.POST.get("name",""),
        "path"  : request.POST.get("path",""),
        "breed" : request.POST.get("breed",""),
        "arch"  : request.POST.get("arch","")
        }
    oauth.remote.background_import(options,request.session['cobbler_token'])
    return HttpResponseRedirect('/quick/task_created')

# ======================================================================

def ksfile_list(request, page=None):
    """
    List all kickstart templates and link to their edit pages.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/ksfile/list", expired=True)
    ksfiles = oauth.remote.get_kickstart_templates(request.session['cobbler_token'])
 
    ksfile_list = []
    for ksfile in ksfiles:
        # filter out non-editable, but valid, values
        if ksfile not in ["", "<<inherit>>"]:
            ksfile_list.append((ksfile, ksfile, 'editable'))
 
    t = get_template('ksfile_list.tmpl')
    html = t.render(RequestContext(request,{
        'what':'ksfile',
        'ksfiles': ksfile_list,
        'version': oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'item_count': len(ksfile_list[0]),
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

# ======================================================================

@csrf_protect
def ksfile_edit(request, ksfile_name=None, editmode='edit'):
    """
    This is the page where a kickstart file is edited.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/ksfile/edit/file:%s" % ksfile_name, expired=True)
    if editmode == 'edit':
        editable = False
    else:
        editable = True
    deleteable = False
    ksdata = ""
    if not ksfile_name is None:
        editable = oauth.remote.check_access_no_fail(request.session['cobbler_token'], "modify_kickstart", ksfile_name)
        deleteable = not oauth.remote.is_kickstart_in_use(ksfile_name, request.session['cobbler_token'])
        ksdata = oauth.remote.read_or_write_kickstart_template(ksfile_name, True, "", request.session['cobbler_token'])
 
    t = get_template('ksfile_edit.tmpl')
    html = t.render(RequestContext(request,{
        'ksfile_name' : ksfile_name,
        'deleteable'  : deleteable,
        'ksdata'      : ksdata,
        'editable'    : editable,
        'editmode'    : editmode,
        'version'     : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

# ======================================================================

@require_POST
@csrf_protect
def ksfile_save(request):
    """
    This page processes and saves edits to a kickstart file.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/ksfile/list", expired=True)
    # FIXME: error checking
 
    editmode = request.POST.get('editmode', 'edit')
    ksfile_name = request.POST.get('ksfile_name', None)
    ksdata = request.POST.get('ksdata', "").replace('\r\n','\n')
    if ksfile_name == '':
        return error_page(request,"模板名字不能为空!")
    if editmode != 'edit':
        ksfile_name = "/var/lib/cobbler/kickstarts/" + ksfile_name
 
    delete1   = request.POST.get('delete1', None)
    delete2   = request.POST.get('delete2', None)
 
    if delete1 and delete2:
        oauth.remote.read_or_write_kickstart_template(ksfile_name, False, -1, request.session['cobbler_token'])
        return HttpResponseRedirect('/quick/ksfile/list')
    else:
        oauth.remote.read_or_write_kickstart_template(ksfile_name,False,ksdata,request.session['cobbler_token'])
        return HttpResponseRedirect('/quick/ksfile/list')

# ======================================================================

def snippet_list(request, page=None):
    """
    This page lists all available snippets and has links to edit them.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/snippet/list", expired=True)
    snippets = oauth.remote.get_snippets(request.session['cobbler_token'])
 
    snippet_list = []
    base_dir = "/var/lib/cobbler/snippets/"
    for snippet in snippets:
        if snippet.startswith(base_dir):
            snippet_list.append((snippet, snippet.replace(base_dir, ""), 'editable'))
        else:
            return error_page(request, "Invalid snippet at %s, outside %s" % (snippet, base_dir))
 
    t = get_template('snippet_list.tmpl')
    html = t.render(RequestContext(request,{
        'what'     : 'snippet',
        'snippets' : snippet_list,
        'version'  : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

# ======================================================================

@csrf_protect
def snippet_edit(request, snippet_name=None, editmode='edit'):
    """
    This page edits a specific snippet.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/edit/file:%s" % snippet_name, expired=True)
    if editmode == 'edit':
        editable = False
    else:
        editable = True
    deleteable = False
    snippetdata = ""
    if not snippet_name is None:
        editable = oauth.remote.check_access_no_fail(request.session['cobbler_token'], "modify_snippet", snippet_name)
        deleteable = True
        snippetdata = oauth.remote.read_or_write_snippet(snippet_name, True, "", request.session['cobbler_token'])
 
    t = get_template('snippet_edit.tmpl')
    html = t.render(RequestContext(request,{
        'snippet_name' : snippet_name,
        'deleteable'   : deleteable,
        'snippetdata'  : snippetdata,
        'editable'     : editable,
        'editmode'     : editmode,
        'version'      : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

# ======================================================================

@require_POST
@csrf_protect
def snippet_save(request):
    """
    This snippet saves a snippet once edited.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/snippet/list", expired=True)
    # FIXME: error checking
 
    editmode = request.POST.get('editmode', 'edit')
    snippet_name = request.POST.get('snippet_name', '')
    snippetdata = request.POST.get('snippetdata', "").replace('\r\n','\n')
 
    if snippet_name == '':
        return error_page(request,"SNIPPET名字不能为空!")
    if editmode != 'edit':
       if snippet_name.find("/var/lib/cobbler/snippets/") != 0:
            snippet_name = "/var/lib/cobbler/snippets/" + snippet_name
 
    delete1   = request.POST.get('delete1', None)
    delete2   = request.POST.get('delete2', None)
 
    if delete1 and delete2:
        oauth.remote.read_or_write_snippet(snippet_name, False, -1, request.session['cobbler_token'])
        return HttpResponseRedirect('/quick/snippet/list')
    else:
        oauth.remote.read_or_write_snippet(snippet_name,False,snippetdata,request.session['cobbler_token'])
        return HttpResponseRedirect('/quick/snippet/list')

# ======================================================================

def setting_list(request):
    """
    This page presents a list of all the settings to the user.  They are not editable.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/setting/list", expired=True)
    settings = oauth.remote.get_settings()
    skeys = settings.keys()
    skeys.sort()

    results = []
    for k in skeys:
        results.append([k,settings[k]])

    t = get_template('settings.tmpl')
    html = t.render(RequestContext(request,{
         'settings' : results,
         'version'  : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
         'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

@csrf_protect
def setting_edit(request, setting_name=None):
    if not setting_name:
        return HttpResponseRedirect('/quick/setting/list')
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/setting/edit/%s" % setting_name, expired=True)

    settings = oauth.remote.get_settings()
    if not settings.has_key(setting_name):
        return error_page(request,"Unknown setting: %s" % setting_name)

    cur_setting = {
        'name'  : setting_name,
        'value' : settings[setting_name],
    }

    fields = get_fields('setting', False, seed_item=cur_setting)
    sections = {}
    for field in fields:
        bmo = field_info.BLOCK_MAPPINGS_ORDER[field['block_section']]
        fkey = "%d_%s" % (bmo,field['block_section'])
        if not sections.has_key(fkey):
            sections[fkey] = {}
            sections[fkey]['name'] = field['block_section']
            sections[fkey]['fields'] = []
        sections[fkey]['fields'].append(field)

    t = get_template('generic_edit.tmpl')
    html = t.render(RequestContext(request,{
        'what'            : 'setting',
        #'fields'          : fields,
        'sections'        : sections,
        'subobject'       : False,
        'editmode'        : 'edit',
        'editable'        : True,
        'version'         : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'name'            : setting_name,
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

@csrf_protect
def setting_save(request):
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/setting/list", expired=True)

    # load request fields and see if they are valid
    setting_name = request.POST.get('name', "")
    setting_value = request.POST.get('value', None)

    if setting_name == "":
        return error_page(request,"The setting name was not specified")

    settings = oauth.remote.get_settings()
    if not settings.has_key(setting_name):
        return error_page(request,"Unknown setting: %s" % setting_name)

    if oauth.remote.modify_setting(setting_name, setting_value, request.session['cobbler_token']):
        return error_page(request,"There was an error saving the setting")

    return HttpResponseRedirect("/quick/setting/list")

# ======================================================================

def events(request):
    """
    This page presents a list of all the events and links to the event log viewer.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/events", expired=True)
    events = oauth.remote.get_events()
 
    events2 = []
    for id in events.keys():
       (ttime, name, state, read_by) = events[id]
       events2.append([id,time.asctime(time.localtime(ttime)),name,state])
 
    def sorter(a,b):
       return cmp(a[0],b[0])
    events2.sort(sorter)
 
    t = get_template('events.tmpl')
    html = t.render(RequestContext(request,{
        'results'  : events2,
        'version'  : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

# ======================================================================

def iplist(request):
    """
    This page presents a list of all the IP addresses
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/iplist", expired=True)
    systems = oauth.remote.get_systems()
    iplist = []
    for system in systems:
       for iname in system["interfaces"]:
          if system["interfaces"][iname]["ip_address"] != "" and system["interfaces"][iname]["interface_type"] != "bond_slave" and system["interfaces"][iname]["interface_type"] != "bridge_slave":
             if system["interfaces"][iname]["dns_name"] != "":
                iplist.append([system["interfaces"][iname]["ip_address"], system["interfaces"][iname]["dns_name"], system["name"], iname, system["interfaces"][iname]["mac_address"]])
             else:
                iplist.append([system["interfaces"][iname]["ip_address"], system["hostname"], system["name"], iname, system["interfaces"][iname]["mac_address"]])

    def sorter(a,b):
       return cmp(ipaddress.ip_address(unicode(a[0])),ipaddress.ip_address(unicode(b[0])))
    iplist.sort(sorter)
 
    t = get_template('iplist.tmpl')
    html = t.render(RequestContext(request,{
        'results'  : iplist,
        'version'  : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
    return HttpResponse(html)

# ======================================================================

def eventlog(request, event=0):
    """
    Shows the log for a given event.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/eventlog/%s" % str(event), expired=True)
    event_info = oauth.remote.get_events()
    if not event_info.has_key(event):
        return error_page(request,"event not found")
 
    data       = event_info[event]
    eventname  = data[0]
    eventtime  = data[1]
    eventstate = data[2]
    eventlog   = oauth.remote.get_event_log(event)
 
    t = get_template('eventlog.tmpl')
    vars = {
       'eventlog'   : eventlog,
       'eventname'  : eventname,
       'eventstate' : eventstate,
       'eventid'    : event,
       'eventtime'  : eventtime,
       'version'    : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'meta' : simplejson.loads(request.session['quick_meta'])
    }
    html = t.render(RequestContext(request,vars))
    return HttpResponse(html)

# ======================================================================

def random_mac(request, virttype="xenpv"):
    """
    Used in an ajax call to fill in a field with a mac address.
    """
    # FIXME: not exposed in UI currently
    if not oauth.test_user_authenticated(request): return login(request, expired=True)
    random_mac = oauth.remote.get_random_mac(virttype, request.session['cobbler_token'])
    return HttpResponse(random_mac)

# ======================================================================

@require_POST
@csrf_protect
def sync(request):
    """
    Runs 'cobbler sync' from the API when the user presses the sync button.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/sync", expired=True)
    oauth.remote.background_sync({"verbose":"True"},request.session['cobbler_token'])
    return HttpResponseRedirect("/quick/task_created")
 
# ======================================================================

@require_POST
@csrf_protect
def reposync(request):
    """
    Syncs all repos that are configured to be synced.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/reposync", expired=True)
    oauth.remote.background_reposync({ "names":"", "tries" : 3},request.session['cobbler_token'])
    return HttpResponseRedirect("/quick/task_created")

# ======================================================================

@require_POST
@csrf_protect
def hardlink(request):
    """
    Hardlinks files between repos and install trees to save space.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/hardlink", expired=True)
    oauth.remote.background_hardlink({},request.session['cobbler_token'])
    return HttpResponseRedirect("/quick/task_created")

# ======================================================================

@require_POST
@csrf_protect
def replicate(request):
    """
    Replicate configuration from the central cobbler server, configured
    in /etc/cobbler/settings (note: this is uni-directional!)
 
    FIXME: this is disabled because we really need a web page to provide options for
    this command.
 
    """
    #settings = oauth.remote.get_settings()
    #options = settings # just load settings from file until we decide to ask user (later?)
    #oauth.remote.background_replicate(options, request.session['cobbler_token'])
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/replicate", expired=True)
    return HttpResponseRedirect("/quick/task_created")

# ======================================================================

def __names_from_dicts(loh,optional=True):
    """
    Tiny helper function.
    Get the names out of an array of hashes that the oauth.remote interface returns.
    """
    results = []
    if optional:
       results.append("<<None>>")
    for x in loh:
       results.append(x["name"])
    results.sort()
    return results

# ======================================================================


@csrf_protect
def generic_edit(request, what=None, obj_name=None, editmode="new"):

    """
    Presents an editor page for any type of object.
    While this is generally standardized, systems are a little bit special.
    """
    target = ""
    if obj_name != None:
        target = "/%s" % obj_name
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/%s/edit%s" % (what,target), expired=True)
 
    obj = None
 
    child = False
    if what == "subprofile":
        what = "profile"
        child = True
 
    if not obj_name is None:
        editable = oauth.remote.check_access_no_fail(request.session['cobbler_token'], "modify_%s" % what, obj_name)
        obj = oauth.remote.get_item(what, obj_name, False)
    else:
        editable = oauth.remote.check_access_no_fail(request.session['cobbler_token'], "new_%s" % what, None)
        obj = None

    interfaces = {}
    if what == "system":
        if obj:
            interfaces = obj.get("interfaces",{})
        else:
            interfaces = {}
 
    fields = get_fields(what, child, obj)

    # populate some select boxes
    # FIXME: we really want to just populate with the names, right?
    if what == "profile":
        if (obj and obj["parent"] not in (None,"")) or child:
            __tweak_field(fields, "parent", "choices", __names_from_dicts(oauth.remote.get_profiles()))
        else:
            __tweak_field(fields, "distro", "choices", __names_from_dicts(oauth.remote.get_distros()))
        __tweak_field(fields, "kickstart", "choices", oauth.remote.get_kickstart_templates())
        __tweak_field(fields, "repos", "choices",     __names_from_dicts(oauth.remote.get_repos()))
    elif what == "system":
        __tweak_field(fields, "profile", "choices",      __names_from_dicts(oauth.remote.get_profiles()))
        __tweak_field(fields, "image", "choices",        __names_from_dicts(oauth.remote.get_images(),optional=True))
        __tweak_field(fields, "kickstart", "choices", oauth.remote.get_kickstart_templates())
    elif what == "mgmtclass":
        __tweak_field(fields, "packages", "choices", __names_from_dicts(oauth.remote.get_packages()))
        __tweak_field(fields, "files", "choices",    __names_from_dicts(oauth.remote.get_files()))
    elif what == "image":
        __tweak_field(fields, "kickstart", "choices", oauth.remote.get_kickstart_templates())
 
    if what in ("distro","profile","system"):
        __tweak_field(fields, "mgmt_classes", "choices", __names_from_dicts(oauth.remote.get_mgmtclasses(),optional=False))
        __tweak_field(fields, "os_version", "choices", oauth.remote.get_valid_os_versions())
        __tweak_field(fields, "breed", "choices", oauth.remote.get_valid_breeds())

    # if editing save the fields in the session for comparison later
    if editmode == "edit":
        request.session['%s_%s' % (what,obj_name)] = fields
 
    sections = {}
    for field in fields:
        bmo = field_info.BLOCK_MAPPINGS_ORDER[field['block_section']]
        fkey = "%d_%s" % (bmo,field['block_section'])
        if not sections.has_key(fkey):
            sections[fkey] = {}
            sections[fkey]['name'] = field['block_section']
            sections[fkey]['fields'] = []
        sections[fkey]['fields'].append(field)
 
    t = get_template('generic_edit.tmpl')
    inames = interfaces.keys()
    inames.sort()
    html = t.render(RequestContext(request,{
        'what'            : what,
        #'fields'          : fields,
        'sections'        : sections,
        'subobject'       : child,
        'editmode'        : editmode,
        'editable'        : editable,
        'interfaces'      : interfaces,
        'interface_names' : inames,
        'interface_length': len(inames),
        'version'         : oauth.remote.extended_version(request.session['cobbler_token'])['version'],
        'name'            : obj_name,
        'meta' : simplejson.loads(request.session['quick_meta'])
    }))
 
    return HttpResponse(html)
# ======================================================================

@require_POST
@csrf_protect
def generic_save(request,what):

    """
    Saves an object back using the cobbler API after clearing any 'generic_edit' page.
    """
    if not oauth.test_user_authenticated(request): return login(request, next="/quick/%s/list" % what, expired=True)

    # load request fields and see if they are valid
    editmode  = request.POST.get('editmode', 'edit')
    obj_name  = request.POST.get('name', "")
    subobject = request.POST.get('subobject', "False")

    if subobject == "False":
        subobject = False
    else:
        subobject = True

    if obj_name == "":
        return error_page(request,"文件名称不能为空")

    prev_fields = []
    if request.session.has_key("%s_%s" % (what,obj_name)) and editmode == "edit":
        prev_fields = request.session["%s_%s" % (what,obj_name)]
    # grab the oauth.remote object handle
    # for edits, fail in the object cannot be found to be edited
    # for new objects, fail if the object already exists
    if editmode == "edit":
        if not oauth.remote.has_item(what, obj_name):
            return error_page(request,"文件不存在或者已被删除")
        obj_id = oauth.remote.get_item_handle( what, obj_name, request.session['cobbler_token'] )
    else:
        if oauth.remote.has_item(what, obj_name):
            return error_page(request,"文件已存在")
        obj_id = oauth.remote.new_item( what, request.session['cobbler_token'] )

    # walk through our fields list saving things we know how to save
    fields = get_fields(what, subobject)

    for field in fields:
        if field['name'] == 'name' and editmode == 'edit':
            # do not attempt renames here
            continue
        elif field['name'].startswith("*"):
            # interface fields will be handled below
            continue
        else:
            # check and see if the value exists in the fields stored in the session
            prev_value = None
            for prev_field in prev_fields:
                if prev_field['name'] == field['name']:
                    prev_value = prev_field['value']
                    break

            value = request.POST.get(field['name'],None)
            # Checkboxes return the value of the field if checked, otherwise None
            # convert to True/False
            if field["html_element"] == "checkbox":
                if value==field['name']:
                    value=True
                else:
                    value=False

            # Multiselect fields are handled differently
            if field["html_element"] == "multiselect":
                values=request.POST.getlist(field['name'])
                value=[]
                if '<<inherit>>' in values:
                    value='<<inherit>>'
                else:
                    for single_value in values:
                        if single_value != "<<None>>":
                            value.insert(0,single_value)

            if value != None:
                if value == "<<None>>":
                    value = ""
                if value is not None and (not subobject or field['name'] != 'distro') and value != prev_value:
                    try:
                        oauth.remote.modify_item(what,obj_id,field['name'],value,request.session['cobbler_token'])
                    except Exception, e:
                        return error_page(request,str(e))

    # special handling for system interface fields
    # which are the only objects in cobbler that will ever work this way
    if what == "system":
        interface_field_list = []
        for field in fields:
            if field['name'].startswith("*"):
                field = field['name'].replace("*","")
                interface_field_list.append(field)
        interfaces = request.POST.get('interface_list', "").split(",")
        for interface in interfaces:
            if interface == "":
                continue
            ifdata = {}
            for item in interface_field_list:
                ifdata["%s-%s" % (item,interface)] = request.POST.get("%s-%s" % (item,interface), "")
            ifdata=utils.strip_none(ifdata)
            # FIXME: I think this button is missing.
            present  = request.POST.get("present-%s" % interface, "")
            original = request.POST.get("original-%s" % interface, "")
            try:
                if present == "0" and original == "1":
                    oauth.remote.modify_system(obj_id, 'delete_interface', interface, request.session['cobbler_token'])
                elif present == "1":
                    oauth.remote.modify_system(obj_id, 'modify_interface', ifdata, request.session['cobbler_token'])
            except Exception, e:
                return error_page(request, str(e))
    try:
        oauth.remote.save_item(what, obj_id, request.session['cobbler_token'], editmode)
    except Exception, e:
        return error_page(request, str(e))

    return HttpResponseRedirect('/quick/%s/list' % what)




