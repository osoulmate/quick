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
2. 安装pip工具
```
yum install -y python-pip
pip install --index http://pypi.douban.com/simple/ paramiko --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ gevent --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ pymysql --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ pyexcel --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ pyexcel-xls --trusted-host pypi.douban.com
pip install --index http://pypi.douban.com/simple/ pyexcel-io --trusted-host pypi.douban.com
```
3. 下载并安装mysql安装源
```
yum install -y wget
wget http://dev.mysql.com/get/mysql-community-release-el7-5.noarch.rpm
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
```
cd /usr/share/quick
mkdir sessions
chown -R apache sessions/                                 #赋予apache用户读写sessions文件夹及其文件的权限
chown apache extend/novnc/vnc_tokens                      #赋予apache用户读写vnc_tokens文件的权限
python manage.py syncdb                                   #创建数据表
mkdir /var/log/quick                                      #创建日志文件夹
chown -R apache /var/log/quick                            #赋予apache用户读写/var/log/quick文件夹及其文件的权限
修改agent目录下两个文件qios2.py qios3.py中QUICK_SERVER的值为本机IP
```
13. 复制quick_content到/var/www/目录下。
14. 复制misc目录下所有文件到/var/www/cobbler/misc/目录下
15. 复制quick.conf到/etc/httpd/conf.d/目录下
16. 复制kickstarts目录下所有文件 到 /var/lib/cobbler/kickstarts/目录下
17. 复制snippets目录下所有文件到/var/lib/cobbler/snippets/目录下
18. 复制scripts目录下所有文件到/var/lib/cobbler/scripts/目录下
19. 重启apache服务
```
systemctl restart httpd
```
20. 创建管理平台登陆账号,使用浏览器访问`http://localhost/quick/add_web_users`
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

在有DHCP网络环境下进行裸机系统安装时，要注意system中是否有多个名字不同的配置文件但主机MAC地址相同的情况。如果有，则要先删除无效的配置文件，否则裸机启动时获得的IP将与要分配的IP不一致。
