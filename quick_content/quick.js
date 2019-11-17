function user_offline(name){
    if (confirm("确认将用户"+name+"踢下线吗?")) {
        document.forms["action"].action = "/quick/user/single/offline/"+name;
        document.forms["action"].submit();
    }
}
function user_delete(name){
    if (confirm("确认删除用户" + name + "吗?")) {
        document.forms["action"].action = "/quick/user/single/delete/"+name
        document.forms["action"].submit();
    }
}
function items_check_all(){
    var checkall = document.getElementById("itemsall").checked
    var items    = document.getElementsByName("items")
    for(i=0; i<items.length; ++i) {
        items[i].checked=checkall;
        items_check(items[i])
    }
}

function items_check(obj) {
    obj.parentNode.parentNode.className=(obj.checked)? 'selected' : '';
}

function items_checked_values() {
    var items = document.getElementsByName("items")
    var values = new Array();
    for(i=0; i<items.length; ++i) {
        if (items[i].checked) {
            values.push(items[i].value)
        }
    }
    s = values.join(" ")
    return s;
}

function obj_delete(old) {
    if (confirm("确认删除任务 (" + old + ") 吗?")) {
        document.forms["action"].action = "/quick/task/delete/" + old;
        document.forms["action"].submit();
    }
}
function obj_execute(taskname) {
    if (confirm("警告！重装操作不可逆！确认执行任务 (" + taskname + ") 吗?")) {
        document.forms["action"].action = "/quick/task/execute/" + taskname;
        document.forms["action"].submit();
    }
}
function action(otype) {
    sel_action = document.getElementById("actions").value
    what   = sel_action.split("|")[0]
    action = sel_action.split("|")[1]
    document.location = "/quick/" + what + "/" + action
}

function action_sort(what,value) {
    document.forms["action"].action = "/quick/" + what + "/modifylist/sort/" + value;
    document.forms["action"].submit();
}

function action_multi(otype) {
    var values = items_checked_values()
    if (values == "") {
       return
    }
    document.getElementById("names").value = values
    sel_batchaction = document.getElementById("batchactions").value
    action = sel_batchaction.split("|")[0]
    param  = sel_batchaction.split("|")[1]

    if ((action == "delete" ) && (param == "delete")) {
        value = confirm("确认删除选中的 " + otype + "吗?" )
    }
    if ((action == "power") && (param == "on")) {
        value = confirm("确认将选中项开机吗?")
    }
    if ((action == "power") && (param == "off")) {
        value = confirm("确认将选中项关机吗?")
    }
    if ((action == "power") && (param == "reboot")) {
        value = confirm("确认将选中项重启吗?")
    }
    if ((action == "pxe") && (param == "boot")) {
        value = confirm("确认将选中项强制从网络启动吗?")
    }
    if ((action == "account") && (param == "enable")) {
        value = confirm("确认将选中项账号启用吗?")
    }
    if ((action == "account") && (param == "disable")) {
        value = confirm("确认将选中项账号禁用吗?")
    }
    if (value) {
        document.myform.action = "/quick/" + otype + "/multi/" + action + "/" + param
        document.myform.submit()  
    }
    else {
        alert("操作取消.")
    }
}
setInterval(function(){ update() }, 1000);
function update() {
    $(".progress").each(function(){
        //console.log($(this).attr("id"))
        //console.log($(this).text())
        if ($(this).text() == '100%' || $(this).text() == '完成'){
            $(this).removeClass("progress")
            $(this).prev().removeClass("usetime")
            return
        }else{
            var progress = $(this).attr("id")
            var task_name = progress.split("|")[0]
            var v = progress.split("|")[1]
            $(this).load("/quick/task/notice/"+task_name+"?k="+v,function(responseTxt,statusTxt,xhr){
                        if(statusTxt=="success")
                        $(this).attr("title",responseTxt)
                        })
            //$(this).attr("title",$(this).text())
        }
    });
    $(".usetime").each(function(){
        //console.log($(this).attr("id"))
        var usetime = $(this).attr("id")
        var task_name = usetime.split("|")[0]
        var v = usetime.split("|")[1]
        $(this).load("/quick/task/notice/"+task_name+"?k="+v)
    });
}
$(function(){
    $("#listitems td[title]").bind("dblclick",function(){
        var input ="<input type='text' id='temp' value='"+$(this).text()+"' >";
        console.log($(this).text())
        //var input ="<input type='text' id='temp' value="+$(this).attr('title')+" >";
        //console.log($(this).attr('title'))
        //var input = "<textarea id='temp'>"+$(this).text()+"</textarea>";
        $(this).text("");
        $(this).append(input);
        $("input#temp").focus();
        $("input").blur(function(){
            if($(this).val()==""){
                $(this).remove();
            }else{
                $(this).closest("td").text($(this).val());
            }
        });
    });
})
