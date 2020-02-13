/*
var run_once = 0
var now = new Date()
var page_load = -1
*/
/* show tasks not yet recorded, update task found time in hidden field */
function get_latest_task_info() {
  var username = document.getElementById("username").value

  /* FIXME: used the logged in user here instead */
  /* FIXME: don't show events that are older than 40 seconds */
  $.getJSON("/cblr/svc/op/events/user/" + username,
    function(data){$.each(data, function(i,record) {
        var id = record[0];
        var ts = record[1];
        var name = record[2];
        var state = record[3];
        var buf = ""
        var logmsg = " <a href=\"/quick/eventlog/" + id + "\">日志详情</A>";
        if (state == "complete") {
          buf = "任务" + name + " 已完成: " + logmsg
        }
        else if (state == "running") {
          buf = "任务 " + name + "正在执行: " + logmsg
        }
        else if (state == "failed") {
          buf = "任务 " + name + " 执行失败: " + logmsg
        }
        else {
          buf = name
        }
        var placementFrom = 'top'; /*bottom*/
        var placementAlign = 'right'; /*left center*/
        var state = 'info'; /*default primary secondary success warning danger */
        var style = 'plain'; /*withicon*/
        var content = {};
        content.message = buf;
        content.title = '系统通知';
        if (style == "withicon") {
            content.icon = 'fa fa-bell';
        } else {
            content.icon = 'none';
        }
        content.url = '/quick/eventlog/'+ id;
        content.target = '_blank';
        $.notify(content,{
            type: state,
            placement: {
                from: placementFrom,
                align: placementAlign
            },
            time: 1000,
            delay: 5000,
        });
    });
  });
}

function update() {
    $(".quick-progress").each(function(){
        //console.log($(this).attr("id"))
        //console.log($(this).text())
        if ($(this).text() == '100%' || $(this).text() == '完成'){
            $(this).removeClass("quick-progress")
            $(this).prev().removeClass("quick-usetime")
            return
        }else{
            var progress = $(this).attr("id")
            var task_name = progress.split("|")[0]
            var v = progress.split("|")[1]
            $(this).load("/quick/install/notice/"+task_name+"?k="+v,function(responseTxt,statusTxt,xhr){
                        if(statusTxt=="success")
                        $(this).attr("title",responseTxt)
                        })
            //$(this).attr("title",$(this).text())
        }
    });
    $(".quick-usetime").each(function(){
        //console.log($(this).attr("id"))
        var usetime = $(this).attr("id")
        var task_name = usetime.split("|")[0]
        var v = usetime.split("|")[1]
        $(this).load("/quick/install/notice/"+task_name+"?k="+v)
    });
}

function go_go_gadget() {
    setInterval(get_latest_task_info,2000)
    setInterval(function(){ update() }, 1000);
    top.document.getElementById("paneloading").style.display = "none";
    try {
       page_onload()
    } 
    catch (error) {
    }
}

function page_onload() { 
    var submitting = false;
    $(window).bind("submit", function () {
        submitting = true;
    });
    $(window).bind("beforeunload", function () {
       if (!submitting && $("#ksdata")[0].defaultValue !== $("#ksdata")[0].value) {
            submitting = false;
            return "您有未保存的更改";
       }
    });
}

function items_check_all(){
    var checkall = document.getElementById("itemsall").checked
    var items    = document.getElementsByName("items")
    for(i=0; i<items.length; ++i) {
        items[i].checked=checkall;
        items_check(items[i])
    }
}
function item_check_off(obj,num,what){
    //console.log(num)
    //console.log(obj.id)
    var num = Number(num)
    var view = ''
    if (obj.checked ? 'selected' : ''){
        $('table thead tr').find("th:eq("+num+")").show();
        $('table tbody tr').find("td:eq("+num+")").show();
        view = 'on'
    }else{
        $('table thead tr').find("th:eq("+num+")").hide();
        $('table tbody tr').find("td:eq("+num+")").hide();
        view = 'off'
    }
    var csrfToken = $("[name='csrfmiddlewaretoken']").val();
    $.ajax({
      url: "/quick/ajax",
      type: "POST",
      headers: {"X-CSRFToken": csrfToken},
      data: {
        what  : what,
        name  : obj.id,
        view  : view,
        action: "update_view_col"
       },
      success: function (data,status) {
        //console.log("数据: \n" + data + "\n状态: " + status);
      }
    })
}
/*
function display(){
    $('#view_col').css('display',''); 
}
function hide(){
    $('#view_col').css('display','none'); 
}*/
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

function obj_execute(target,msg,para){
    confirm({
            target: target,
            para  : para,
            msg   : msg
            });
}
function obj_rename(what,old) {
    var newname = window.prompt("请填写新的名字",old);
    if (newname != null) {
        document.forms["action"].action = "/quick/" + what + "/rename/" + old + "/" + newname;
        document.forms["action"].submit();
    }
}
function obj_copy(what,old) {
    var newname = window.prompt("请填写新的名字",old);
    if (newname != null) {
        document.forms["action"].action = "/quick/" + what + "/copy/" + old + "/" + newname;
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
    target = "/quick/" + otype + "/multi/" + action + "/" + param
    if ((action == "delete" ) && (param == "delete")) {
        msg = "确认删除?" 
    }
    if ((action == "power") && (param == "on")) {
        msg = "确认开机?" 
    }
    if ((action == "power") && (param == "off")) {
        msg = "确认关机?"
    }
    if ((action == "power") && (param == "reboot")) {
        msg = "确认重启?"
    }
    if ((action == "pxe") && (param == "boot")) {
        msg = "确认PXE启动?"
    }
    if ((action == "account") && (param == "enable")) {
        msg = "确认启用账号?"
    }
    if ((action == "account") && (param == "disable")) {
        msg = "确认禁用账号?"
    }
    if (action == "profile") {
        param = window.prompt("请输入新的名字","")
        if ((param == null) || (param == "")) {
            return
        }
        msg = "确认修改?"
    }
    if ((action == "netboot") && (param == "enable")) {
        msg = "确认启用网络启动功能?"
    }
    if ((action == "netboot") && (param == "disable")) {
        msg = "确认禁用网络启动功能?"
    }
    if ((action == "buildiso" ) && (param == "enable")) {
        msg = "确认bulid iso?"
    }
    if ((action == "reposync")) {
        msg = "确认进行repo同步?"
    }
    if(msg)
    {
        confirm({
                target: target,
                para  : 'myform',
                msg   : msg
                });
    }else{
        return;
    }
}
function action_multi_new(otype) {
    var values = items_checked_values()
    console.log(values)
    if (values == "") {
       return
    }
    document.getElementById("names").value = values
    sel_batchaction = document.getElementById("batchactions").attributes['value'].value
    console.log(sel_batchaction)
    action = sel_batchaction.split("|")[0]
    param  = sel_batchaction.split("|")[1]
    target = "/quick/" + otype + "/multi/" + action + "/" + param
    if ((action == "delete" ) && (param == "delete")) {
        msg = "确认删除?" 
    }
    if(msg)
    {
        confirm({
                target: target,
                para  : 'myform',
                msg   : msg
                });
    }else{
        return;
    }
}
/*
function get_data(what){
    $.getJSON("/quick/ajax/"+what,function(result){
        $.each(result, function(i, field){
            console.log(field['fields'])
        });
    });
}
*/
function batch_query(what){
    //设置遮罩层，可防止用户确认提示框前选择页面其它元素。
    if (what == 'asset/hardware'){
        str = '请输入查询SN'
    }else{
        str = '请输入查询IP'
    }
    var shield = document.createElement("DIV");
    shield.id = "shield";
    shield.style.position = "absolute";
    shield.style.left = "0px";
    shield.style.top = "0px";
    shield.style.width = "100%";
    shield.style.height = document.body.scrollHeight+"px";
    shield.style.background = "#b3b3b3";
    shield.style.textAlign = "center";
    shield.style.zIndex = "10000";
    shield.style.opacity = "0.1";
    shield.style.filter = "alpha(opacity=10)";
    var inputFram = document.createElement("DIV");
    inputFram.id="inputFram";
    inputFram.style.position = "absolute";
    inputFram.style.top = "30%";
    inputFram.style.left = "27%";
    inputFram.style.width = "46%";
    inputFram.style.height = "45%";
    inputFram.style.background = "white";
    inputFram.style.zIndex = "10001";
    strHtml = "<ul style=\"list-style:none;margin:0px;padding:0px;width:100%;height:100%\">\n";
    strHtml += " <li style=\"text-align:left;font-size:18px;height:10%;background-color:#f4f4f4;padding-top:10px;padding-left:8px;\">"+str+"</li>\n";
    strHtml += " <li style=\"text-align:center;font:normal bold 18px/30px arial,sans-serif;height:65%;padding-top:5px;\"><textarea style=\"width:95%;height:100%;\" id=\"ippool\" name=\"ippool\"></textarea></li>\n";
    strHtml += " <li style=\"position:absolute;bottom:5px;right:20px;font-weight:bold;height:10%;\"><input type=\"button\" value=\"确 定\" class=\"ack-btn\" style=\"background-color:#1e9fff;\" onclick=\"ok('确认')\" /><input type=\"button\" value=\"取消\" class=\"cancel-btn\" onclick=\"cancel('取消')\" /></li>\n";
    strHtml += "</ul>\n";
    inputFram.innerHTML = strHtml;
    document.body.appendChild(inputFram);
    document.body.appendChild(shield);
    this.ok = function(){
        inputFram.style.display = "none";
        shield.style.display = "none";
        var ippool = document.getElementById("ippool").value
        ippool = ippool.replace(/\r\n/g,",")
        ippool = ippool.replace(/\n/g,",")
        console.log(ippool)
        document.forms['action'].action = '/quick/'+what+"/list?ippool="+ippool;
        document.forms['action'].submit();
    }
    this.cancel = function(){
        inputFram.style.display = "none";
        shield.style.display = "none";
    }
    inputFram.focus();
}
jQuery.expr[':'].contains = function (a, i, m) {
    return jQuery(a).text().toUpperCase()
        .indexOf(m[3].toUpperCase()) >= 0;
};
$(document).ready(function(){
    $("#filter_value").keyup(function () {
        console.log($("#filter_value").attr("name"))
        var what = $("#filter_value").attr("name").split("|")[1]
        try {
            get_data(what)
        } 
        catch (error) {
        }
        $("table tbody tr").stop().hide()
        console.log('filter')
        $("table tbody tr").filter(":contains('"+($(this).val())+"')").show();
    });
    $("table td[title]").bind("dblclick",function(){
        var input ="<input type='text' id='temp' value='"+$(this).text()+"' >";
        console.log($(this).text())
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
});

function loading(){
    //当点击资产管理下各视图链接时触发该功能
    top.document.getElementById("paneloading").style.display = "";
}
window.confirm = function(option)
{
    var msg = option.msg;
    console.log('msg is '+msg)
    var target = option.target;
    console.log('target is '+target)
    var para = option.para;
    console.log('para is '+para)
    //设置遮罩层，可防止用户确认提示框前选择页面其它元素。
    var shield = document.createElement("DIV");
    shield.id = "shield";
    shield.style.position = "absolute";
    shield.style.left = "0px";
    shield.style.top = "0px";
    shield.style.width = "100%";
    shield.style.height = document.body.scrollHeight+"px";
    shield.style.background = "#b3b3b3";
    shield.style.textAlign = "center";
    shield.style.zIndex = "10000";
    shield.style.opacity = "0.1";
    shield.style.filter = "alpha(opacity=10)";
    var alertFram = document.createElement("DIV");
    alertFram.id="alertFram";
    alertFram.style.position = "absolute";
    alertFram.style.top = "35%";
    alertFram.style.left = "40%";
    alertFram.style.width = "20%";
    alertFram.style.height = "30%";
    alertFram.style.background = "white";
    alertFram.style.zIndex = "10001";
    strHtml = "<ul style=\"list-style:none;margin:0px;padding:0px;width:100%\">\n";
    strHtml += " <li style=\"text-align:left;font-size:18px;height:30px;background-color:#f4f4f4;padding-top:7px;padding-left:8px;\">提示!</li>\n";
    strHtml += " <li style=\"text-align:center;font:normal bold 18px/30px arial,sans-serif;height:40px;padding-top:20px;\">"+msg+"</li>\n";
    strHtml += " <li style=\"position:absolute;bottom:10px;right:20px;font-weight:bold;height:25px;\"><input type=\"button\" value=\"确 定\" class=\"ack-btn\" style=\"background-color:#1e9fff;\" onclick=\"ok('确认')\" /><input type=\"button\" value=\"取消\" class=\"cancel-btn\" onclick=\"cancel('取消')\" /></li>\n";
    strHtml += "</ul>\n";
    alertFram.innerHTML = strHtml;
    document.body.appendChild(alertFram);
    document.body.appendChild(shield);
    this.ok = function(){
        alertFram.style.display = "none";
        shield.style.display = "none";
        //console.log("you click ok in this.ok")
        document.forms[para].action = target;
        //console.log(document.forms["action"].action )
        document.forms[para].submit();
    }
    this.cancel = function(){
        alertFram.style.display = "none";
        shield.style.display = "none";
    }
    alertFram.focus();
}


