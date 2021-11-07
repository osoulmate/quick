sed -i "s/server: 127.0.0.1/server: $QUICK_SERVER/g" /etc/cobbler/settings
sed -i "s/next_server: 127.0.0.1/next_server: $QUICK_SERVER/g" /etc/cobbler/settings
sed -i "s/QUICK_SERVER = '172.16.1.10'/QUICK_SERVER='$QUICK_SERVER'/g" /usr/share/quick/agent/qios2.py
sed -i "s/QUICK_SERVER = '172.16.1.10'/QUICK_SERVER='$QUICK_SERVER'/g" /usr/share/quick/agent/qios3.py
sed -i "s/172.16.1.10/$QUICK_SERVER/g" /var/www/quick_content/bootos/pxelinux.cfg/default
sed -i "s/filename \"pxelinux.0\"/filename \"undionly.kpxe\"/g" /etc/cobbler/dhcp.template
sed -i "s/subnet 192.168.1.0 netmask 255.255.255.0/subnet $DHCP_SUBNET netmask $DHCP_NETMASK/g" /etc/cobbler/dhcp.template
sed -i "s/option routers             192.168.1.5/option routers             $DHCP_ROUTERS/g" /etc/cobbler/dhcp.template
sed -i "s/option domain-name-servers 192.168.1.1/option domain-name-servers $DHCP_DNS/g" /etc/cobbler/dhcp.template
sed -i "s/option subnet-mask         255.255.255.0/option subnet-mask         $DHCP_NETMASK/g" /etc/cobbler/dhcp.template
sed -i "s/range dynamic-bootp        192.168.1.100 192.168.1.254/range dynamic-bootp        $DHCP_SUBNET_RANGE/g" /etc/cobbler/dhcp.template
mysql -e 'create database quick'
mysql -e "set password for 'root'@'localhost'=password('root');"
echo 'no'|python /usr/share/quick/manage.py syncdb
cobbler import --name=centos7.3 --path=/mnt --kickstart=/var/lib/cobbler/kickstarts/quick_sample.ks
service cobblerd restart
cobbler sync