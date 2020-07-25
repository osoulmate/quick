# quick
a platform of os management base Cobbler web
---
**系统要求**: centos7

**硬件要求**: x86，内存4G以上，硬盘容量不低于100G

**软件环境**: Django 1.6.11.7  MySQL Ver 14.14  Cobbler 2.8.4  node 10.16.0 noVNC WebSSH2

             paramiko  gevent  pymysql  dhcp  tftp  rsync  apache

---
#### 安装流程:

1. 安装epel源
```
yum install -y epel-release
```
2. 安装依赖包
```
yum install -y python-pip
pip install --index http://pypi.douban.com/simple/ paramiko --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ gevent --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ pymysql --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ pyvmomi --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ pyexcel --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ pyexcel-xls --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ pyexcel-io --trusted-host pypi.douban.com
```
3. 下载并安装mysql安装源
```
curl -L http://dev.mysql.com/get/mysql-community-release-el7-5.noarch.rpm -o mysql-community-release-el7-5.noarch.rpm
rpm -ivh mysql-community-release-el7-5.noarch.rpm 
```
4. 安装node版本管理工具nvm
```
curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.33.8/install.sh | bash
source ~/.bashrc
```
5. 安装node
```
nvm install 10.16.0
```
6. 安装forever
```
npm install forever -g --registry=https://registry.npm.taobao.org
```
7. 安装cobbler,dhcp,apache,tftp,xinedtd,django,mysql
```
yum install -y cobbler dhcp xinetd tftp
yum install -y python2-django16-1.6.11.7-5.el7.noarch
yum install -y mysql-community-server
```
8. 配置cobbler
```
systemctl disable firewalld 
systemctl stop firewalld 
setenforce 0
sed -i 's/SELINUX=permissive/SELINUX=disabled/g' /etc/sysconfig/selinux 
sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/sysconfig/selinux 
read -p "please input your active IP ADDRESS: "  my_host                           
sed -i "s/server: 127.0.0.1/server: $my_host/g" /etc/cobbler/settings              
sed -i "s/next_server: 127.0.0.1/next_server: $my_host/g" /etc/cobbler/settings    
sed -i "s/manage_rsync: 0/manage_rsync: 1/g" /etc/cobbler/settings                 
sed -i "s/anamon_enabled: 0/anamon_enabled: 1/g" /etc/cobbler/settings 
systemctl enable cobblerd
systemctl enable httpd
systemctl enable xinetd
systemctl enable tftp
systemctl enable rsyncd
systemctl start tftp
systemctl start rsyncd
systemctl start httpd
systemctl start cobblerd
```
9. 修改/etc/cobbler/dhcp.template配置，添加一个与本机地址在同一个网络的dhcp地址池
```
# ******************************************************************
# Cobbler managed dhcpd.conf file
#
# generated from cobbler dhcp.conf template ($date)
# Do NOT make changes to /etc/dhcpd.conf. Instead, make your changes
# in /etc/cobbler/dhcp.template, as /etc/dhcpd.conf will be
# overwritten.
#
# ******************************************************************

ddns-update-style interim;

allow booting;
allow bootp;

ignore client-updates;
set vendorclass = option vendor-class-identifier;

option pxe-system-type code 93 = unsigned integer 16;

subnet 172.16.1.0 netmask 255.255.255.0 {
     option routers             172.16.1.1;
     option domain-name-servers 172.16.1.1;
     option subnet-mask         255.255.255.0;
     range dynamic-bootp        172.16.1.11 172.16.1.100;
     default-lease-time         21600;
     max-lease-time             43200;
     next-server                $next_server;
     class "pxeclients" {
          match if substring (option vendor-class-identifier, 0, 9) = "PXEClient";
          if option pxe-system-type = 00:02 {
                  filename "ia64/elilo.efi";
          } else if option pxe-system-type = 00:06 {
                  filename "grub/grub-x86.efi";
          } else if option pxe-system-type = 00:07 {
                  filename "grub/grub-x86_64.efi";
          } else if option pxe-system-type = 00:09 {
                  filename "grub/grub-x86_64.efi";
          } else {
                  filename "undionly.kpxe";
          }
     }

}

#for dhcp_tag in $dhcp_tags.keys():
    ## group could be subnet if your dhcp tags line up with your subnets
    ## or really any valid dhcpd.conf construct ... if you only use the
    ## default dhcp tag in cobbler, the group block can be deleted for a
    ## flat configuration
# group for Cobbler DHCP tag: $dhcp_tag
group {
        #for mac in $dhcp_tags[$dhcp_tag].keys():
            #set iface = $dhcp_tags[$dhcp_tag][$mac]
    host $iface.name {
        #if $iface.interface_type == "infiniband":
        option dhcp-client-identifier = $mac;
        #else
        hardware ethernet $mac;
        #end if
        #if $iface.ip_address:
        fixed-address $iface.ip_address;
        #end if
        #if $iface.hostname:
        option host-name "$iface.hostname";
        #end if
        #if $iface.netmask:
        option subnet-mask $iface.netmask;
        #end if
        #if $iface.gateway:
        option routers $iface.gateway;
        #end if
        #if $iface.enable_gpxe:
        if exists user-class and option user-class = "gPXE" {
            filename "http://$cobbler_server/cblr/svc/op/gpxe/system/$iface.owner";
        } else if exists user-class and option user-class = "iPXE" {
            filename "http://$cobbler_server/cblr/svc/op/gpxe/system/$iface.owner";
        } else {
            filename "undionly.kpxe";
        }
        #else
        filename "$iface.filename";
        #end if
        ## Cobbler defaults to $next_server, but some users
        ## may like to use $iface.system.server for proxied setups
        next-server $next_server;
        ## next-server $iface.next_server;
    }
        #end for
}
#end for
```

10. 执行cobbler sync命令，同步配置

11. 启动并配置mysql
```
cat >> /etc/my.cnf <<EOF
[client]
default-character-set = utf8
[mysqld]
default-storage-engine = INNODB
character-set-server = utf8
collation-server = utf8_general_ci
EOF
service mysqld start
mysql -u root
mysql> set password for 'root'@'localhost' =password('root');       #配置数据库访问密码
mysql> grant all privileges on *.* to root@'%'identified by 'root'; #把所有数据库的所有表的所有权限赋值给位于所有IP地址的root用户
mysql> create database quick;
```
12. 复制 quick 文件夹到/usr/share目录下
13. 复制quick_content到/var/www/目录下。
14. 复制misc目录下所有文件到/var/www/cobbler/misc/目录下
15. 复制quick.conf到/etc/httpd/conf.d/目录下
16. 复制kickstarts目录下所有文件到/var/lib/cobbler/kickstarts/目录下
17. 复制snippets目录下所有文件到/var/lib/cobbler/snippets/目录下
18. 复制scripts目录下所有文件到/var/lib/cobbler/scripts/目录下

```
cd /usr/share/quick
chown apache extend/novnc/vnc_tokens                      #赋予apache用户读写vnc_tokens文件的权限
python manage.py syncdb                                   #创建数据表
mkdir /var/log/quick                                      #创建日志文件夹
chown -R apache /var/log/quick                            #赋予apache用户读写/var/log/quick文件夹及其文件的权限
chown -R apache /var/www/quick_content/temp               #赋予apache用户读写/var/www/quick_content/temp文件夹及其文件的权限
修改agent目录下两个文件qios2.py qios3.py中QUICK_SERVER的值为本机IP
```

19. 重启apache服务
```
systemctl restart httpd
```
20. 创建管理平台登陆账号,使用浏览器访问`http://localhost/quick/init`
21. 启动webssh服务
```
forever start /usr/share/quick/extend/webssh2/index.js
```
22. 启动novnc服务
```
复制bin文件夹下novnc文件到/usr/bin/目录下
复制novnc.service文件到/usr/lib/systemd/system/目录下
chmod +x /usr/bin/novnc                               #赋予novnc文件可执行权限
service novnc start                                   #启动novnc服务
```
23. 添加定时任务，清除过期会话
```
*/1 * * * * /usr/bin/python2 /usr/share/quick/manage.py clearsessions >> /var/log/quick/sessions.log
```
24. 登陆平台
    使用浏览器访问http://localhost/quick

**Tips**

1. 在有DHCP网络环境下进行裸机系统安装时，要注意system中是否有多个名字不同的配置文件但主机MAC地址相同的情况。如果有，则要先删除无效的配置文件，否则裸机启动时获得的IP将与要分配的IP不一致。

2. 裸机新装场景下，创建新的装机任务时，最好先将旧的system配置文件删除，并同步下配置(cobbler sync)。当前BootOS内置的代理程序会根据启动命令行中enable_kexec的参数值来判断硬件配置完成后的处理逻辑。参数值为[redhat|suse|ubuntu]，参数值以`/`分割。当安装的目标系统是redhat发行版时，如果enable_kexec的参数值含有redhat，那么硬件配置完成后，代理程序将通过`kexec -e`进行系统安装，否则，代理程序将强制客户机重启。重启后，由于服务端已有该客户机的配置，再次PXE启动将直接进行安装进程。

**待改进**

1. qios2.py,qios3.py 取消当前直接将cobbler接口地址，用户名，密码直接暴露给客户端的方式，改由客户端通过POST请求将所需数据发送给服务端，由服务端验证客户端身份后进行配置，服务端可以根据请求IP、请求MAC是否在本地CMDB数据库中进行主机身份验证。验证通过，则根据主机提交的数据进行配置，配置成功后，响应客户端json格式数据。客户端（即qios2.py或qios3.py）根据回复结果进行后续处理。该API接口为:`quick/api/request_to_config`

2. 新增下载qios2.py,qios3.py的方法，该API接口为:`quick/qios2`,`quick/qios3`

3. 任务详情、任务列表下已用时间和状态字段的AJAX更新请求取消当前的由各个任务或各个主机单独发送更新请求的方式，改由统一的AJAX更新进行更新请求。获取的结果再由客户端JS进行对应视图的更新，以减少服务器的开销。统一的AJAX请求API接口为`quick/api/status`。当从服务端获知当前已没有在执行的任务时，AJAX请求将停止

4. 虚拟化功能的完善

5. 完善各视图的操作日志记录
