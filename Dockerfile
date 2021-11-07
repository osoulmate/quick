FROM centos:centos7.9.2009
MAINTAINER osoulmate <askqingya@gmail.com>
ENV QUICK_SERVER 127.0.0.1
ENV DHCP_SUBNET 172.16.1.0
ENV DHCP_NETMASK 255.255.255.0
ENV DHCP_ROUTERS 172.16.1.1
ENV DHCP_DNS 172.16.1.1
ENV DHCP_SUBNET_RANGE "172.16.1.100 172.16.1.200"
RUN yum install -y epel-release\
    && yum install -y python-pip cobbler python2-django16 dhcp xinetd
RUN curl -L http://dev.mysql.com/get/mysql-community-release-el7-5.noarch.rpm -o mysql-community-release-el7-5.noarch.rpm\
    && rpm -ivh mysql-community-release-el7-5.noarch.rpm\
    && yum install -y –nogpgcheck mysql-community-server
ADD quick/quick /usr/share/quick
ADD quick/extend/node-v10.16.0-linux-x64 /usr/share/node-v10.16.0 
ADD quick/bin/quick.conf /etc/httpd/conf.d/ 
ADD quick/bin/novnc /usr/bin/
ADD quick/bin/novnc.service /usr/lib/systemd/system 
ADD quick/bin/webssh2.service /usr/lib/systemd/system
ADD quick/bin/start.sh /root/
ADD quick/quick_content /var/www/quick_content
ADD quick/misc/ /var/www/cobbler/misc/
ADD quick/kickstarts  /var/lib/cobbler/kickstarts
ADD quick/snippets  /var/lib/cobbler/snippets
ADD quick/scripts  /var/lib/cobbler/scripts
ADD quick/extend/pippkgs /tmp/pippkgs
RUN pip install --verbose  --no-index --find-links=/tmp/pippkgs/ -r /tmp/pippkgs/requirements.txt \
    && chmod 755 -R /usr/share/node-v10.16.0/bin/ \
    && chmod +x /usr/bin/novnc  \
    && ln -s /usr/share/node-v10.16.0/bin/node /usr/local/bin/ \
    && ln -s /usr/share/node-v10.16.0/bin/npm /usr/local/bin/ \
    && cp /var/www/quick_content/bootos/undionly.kpxe /var/lib/tftpboot/ \
    && chown apache:apache /usr/share/quick/extend/novnc/vnc_tokens \
    && mkdir /var/www/quick_content/temp \
    && chown -R apache:apache /var/www/quick_content/temp \
    && mkdir /var/log/quick \
    && chown -R apache:apache /var/log/quick \
    && sed -i '/datadir/adefault-storage-engine=INNODB'  /etc/my.cnf\
    && sed -i '/datadir/acharacter-set-server=utf8'  /etc/my.cnf\
    && sed -i '/datadir/acollation-server=utf8_general_ci'  /etc/my.cnf\
    && sed -i 's/^datadir/#datadir/' /etc/my.cnf\
    && sed -i '/datadir/adatadir=\/data\/mysql/' /etc/my.cnf\
    && mkdir -p /data/mysql \
    && chown mysql:mysql /data/mysql
RUN systemctl enable cobblerd httpd dhcpd novnc webssh2 rsyncd\
    && sed -i -e 's/\(.*disable.*=\) yes/\1 no/' /etc/xinetd.d/tftp\
    && sed -i "s/manage_dhcp: 0/manage_dhcp: 1/g" /etc/cobbler/settings\
    && sed -i "s/manage_rsync: 0/manage_rsync: 1/g" /etc/cobbler/settings\
    && ln -sf "/usr/share/zoneinfo/Asia/Shanghai" /etc/localtime

EXPOSE 69
EXPOSE 80
EXPOSE 443
EXPOSE 8022
EXPOSE 6080
EXPOSE 25151
VOLUME [ "/sys/fs/cgroup" ]
ENTRYPOINT [ "/sbin/init" ]