# quick
a platform of os management base Cobbler web
---
**系统要求**: centos7

**硬件要求**: x86，内存4G以上，硬盘容量不低于100G

**软件环境**: 
```
Django 1.6.11.7  MySQL Ver 14.14  Cobbler 2.8.5  node 10.16.0 noVNC WebSSH2

paramiko  gevent  pymysql  dhcp  tftp  rsync  apache
```

---
#### 容器部署:

1. 下载镜像
```
docker pull osoulmate/quick
```
2. 启动容器 
```
#QUICK_SERVER为HOST IP
#DHCP_SUBNET为与HOST相同子网
#DHCP_NETMASK为与HOST相同子网掩码
#DHCP_ROUTERS为HOST网关
#DHCP_DNS为HOST DNS
docker run -d --privileged --network=host -p 80:80 \
        -e QUICK_SERVER="10.200.30.78"\
        -e DHCP_SUBNET="10.200.30.0" \
        -e DHCP_NETMASK="255.255.255.0" \
        -e DHCP_ROUTERS="10.200.30.78" \
        -e DHCP_DNS="10.200.30.78" \
        -e DHCP_SUBNET_RANGE="10.200.30.100 10.200.30.200" \
        -v /mnt:/mnt  osoulmate/quick
```
3. 挂载centos7.3 x86_64 ISO镜像到HOST /mnt目录下
```
#HOST为虚拟机
mount /dev/sr0 /mnt
#HOST为物理机
mount /dev/cdrom /mnt
```
4. 容器初始化
```
docker exec -it 容器名称/ID /bin/bash
sh /root/start.sh
cobbler sync
```
5. 创建管理平台登陆账号,使用浏览器访问`http://your-host-ip/quick/init`
6. 登陆平台`http://your-host-ip/quick` 用户名:root,密码:rootpwd!

