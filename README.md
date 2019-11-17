# quick
a platform of os management base Cobbler web
---
**系统要求**:    centos7.3(1611)

**硬件要求**:    x86，内存4G以上，硬盘容量不低于100G

**软件环境**:    Django 1.6.11.7

            MySQL Ver 14.14 Distrib 5.6.46
            
            Cobbler 2.8.4
            
            node v10.16.0
            
            paramiko
            
            gevent
            
            pymysql
            
            dhcp
            
            tftp
            
            rsync
            
            apache
---
#### 安装流程:

1. 安装epel源
 ```
 yum install -y epel-release
 ```
2. 安装pip工具
 ```
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py                       #下载pip安装脚本
    python2 get-pip.py                                                            #执行脚本，执行无异常则成功安装pip
    pip install --index http://pypi.douban.com/simple/ paramiko --trusted-host pypi.douban.com
    pip install --index http://pypi.douban.com/simple/ gevent --trusted-host pypi.douban.com
    pip install --index http://pypi.douban.com/simple/ pymysql --trusted-host pypi.douban.com
 ```
