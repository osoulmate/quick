var js_growl = new jsGrowl('js_growl');
var run_once = 0
var now = new Date()
var page_load = -1

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
      /*window.status = buf;*/
      js_growl.addMessage({msg:buf});
    });
  });
  /*$.getJSON("/quick/task/notice/all");*/
}

function go_go_gadget() {
    setInterval(get_latest_task_info,2000)
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
