function setCookie(cname,cvalue,exdays) {
  var d = new Date();
  d.setTime(d.getTime() + (exdays*24*60*60*1000));
  var expires = "expires=" + d.toGMTString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  var name = cname + "=";
  var decodedCookie = decodeURIComponent(document.cookie);
  var ca = decodedCookie.split(';');
  for(var i = 0; i < ca.length; i++) {
    var c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}

function do_login(){
  var userName = $('#username').val();
  var passWord = $('#password').val(); 
  var aa = $("#rememberme").is(":checked");//获取选中状态
  if(userName == ''){    
    console.log("请输入用户名。")
    $("#tips").text("用户名不能为空!")
    return false;
  }    
  if(passWord == ''){
    console.log("请输入密码。");
    $("#tips").text("密码不能为空!")
    return false;
  }
  if(aa==true){
    cname = "yonghuming_"+userName
    setCookie(cname,userName,7)
    cpass = userName +"_mima"
    setCookie(cpass,passWord,7)
  }else{
    cname = "yonghuming_"+userName
    setCookie(cname,'',-1)
    cpass = userName+"_mima"
    setCookie(cpass,'',-1)
  }
  return true;
}
$("#password").focus(function(){
  var userName = $("#username").val()
  var cname = "yonghuming_"+userName
  if(getCookie(cname)){
    cpass = userName + "_mima"
    $('#password').val(getCookie(cpass));
    if($('#password').val()){
      $("#rememberme").prop("checked",true);
    }else{
      $("#rememberme").prop("checked",false);
    }
  }else{
    $('#password').val("")
    $("#rememberme").prop("checked",false);
  }
});
