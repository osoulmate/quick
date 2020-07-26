# quick
a platform of os management base Cobbler web
---
**系统要求**: centos7

**硬件要求**: x86，内存4G以上，硬盘容量不低于100G

**软件环境**: Django 1.6.11.7  MySQL Ver 14.14  Cobbler 2.8.5  node 10.16.0 noVNC WebSSH2

             paramiko  gevent  pymysql  dhcp  tftp  rsync  apache

---
#### 安装流程:

1. 安装epel源和dhcp
```
yum install -y epel-release
yum install -y dhcp
```
2. 安装quick [rpm包下载链接](https://pan.baidu.com/s/18SoD2vkMIXZwJ0n2Qc2rzg) 提取码:ggdi
```
yum install -y quick-1.0.2-1.el7.centos.x86_64.rpm
```
3. 安装mysql
```
curl -L http://dev.mysql.com/get/mysql-community-release-el7-5.noarch.rpm -o mysql-community-release-el7-5.noarch.rpm
rpm -ivh mysql-community-release-el7-5.noarch.rpm 
yum install -y mysql-community-server
```
4. 初始化配置
```
read -p "please input your active IP ADDRESS: "  my_host   
sed -i "s/server: 127.0.0.1/server: $my_host/g" /etc/cobbler/settings              
sed -i "s/next_server: 127.0.0.1/next_server: $my_host/g" /etc/cobbler/settings
sed -i "s/manage_dhcp: 0/manage_dhcp: 1/g" /etc/cobbler/settings    
sed -i "s/manage_rsync: 0/manage_rsync: 1/g" /etc/cobbler/settings
sed -i "s/QUICK_SERVER = '172.16.1.10'/QUICK_SERVER = '$my_host'/g" /usr/share/quick/agent/qios2.py
sed -i "s/QUICK_SERVER = '172.16.1.10'/QUICK_SERVER = '$my_host'/g" /usr/share/quick/agent/qios3.py
sed -i "s/172.16.1.10/$my_host/g" /var/www/quick_content/bootos/pxelinux.cfg/default
cp /var/www/quick_content/bootos/undionly.kpxe /var/lib/tftpboot/
```
5. 修改/etc/cobbler/dhcp.template配置，添加一个与本机地址在同一个网络的dhcp地址池
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
6. 配置并启动mysql
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
mysql> set password for 'root'@'localhost' =password('root');
mysql> grant all privileges on *.* to root@'%'identified by 'root';
mysql> create database quick;
```
7. 创建数据库
```
cd /usr/share/quick
python manage.py syncdb
```
8. 重启并同步cobbler
```
service cobblerd restart
cobbler sync
```
9. 添加定时任务，清除过期会话
```
*/1 * * * * /usr/bin/python2 /usr/share/quick/manage.py clearsessions >> /var/log/quick/sessions.log
```
10. 导入镜像
```
mount /dev/sr0 /mnt #虚拟机环境光驱在系统映射为sr0。请将镜像提前挂载,本例挂载的是centos7.3镜像，你也可以挂载其它系统镜像
cobbler import --name=centos7.3 --path=/mnt --kickstart=/var/lib/cobbler/kickstarts/quick_sample.ks #注意，如果挂载的镜像是x86_64。那么--name名称不用在加上，如为ppc，则--name=centos7.3-ppc。
```
10. 创建管理平台登陆账号,使用浏览器访问`http://localhost/quick/init`
12. 登陆平台`http://localhost/quick` 用户名:root,密码:rootpwd!

