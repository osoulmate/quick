#
# RPM spec file for all Quick packages
#
# Supported/tested build targets:
# - RHEL: 7
# - CentOS: 7

%define apache_etc /etc/httpd/
%define apache_user apache
%define apache_group apache

Name:  quick
Version:  1.0.2
Release:  1%{?dist}
Summary:  quick
Group:    quick
License:  GPLv3
URL:      https://github.com/osoulmate/quick
Source0:  quick-1.0.2.tar.gz
Requires: python-pip,cobbler,python2-django16,dhcp,xinetd
%description
Quick is a platform of os management base Cobbler web
%pre
echo "    Begin to install quick..."
%post
echo "    Begin to configure env..."
chmod 755 /usr/share/node-v10.6.0/bin/*
ln -s /usr/share/node-v10.6.0/bin/node /usr/local/bin/
ln -s /usr/share/node-v10.6.0/bin/npm /usr/local/bin/
cp /var/www/quick_content/bootos/undionly.kpxe /var/lib/tftpboot/
chown apache:apache /usr/share/quick/extend/novnc/vnc_tokens
chown -R apache:apache /var/www/quick_content/temp
chown -R apache:apache /var/log/quick
systemctl disable firewalld 
systemctl stop firewalld 
setenforce 0 > /dev/null
sed -i 's/SELINUX=permissive/SELINUX=disabled/g' /etc/sysconfig/selinux > /dev/null
sed -i 's/SELINUX=enforcing/SELINUX=disabled/g' /etc/sysconfig/selinux > /dev/null
systemctl enable cobblerd
systemctl enable httpd
systemctl enable xinetd
systemctl enable tftp
systemctl enable rsyncd
systemctl enable novnc
systemctl enable node
systemctl start tftp
systemctl start rsyncd
systemctl start httpd
systemctl start cobblerd
systemctl start novnc
systemctl start node
echo "    Begin to install pip packages..."
pip install --verbose  --no-index   --find-links=/tmp/pippkgs/   -r   /tmp/pippkgs/requirements.txt
%preun
echo 'uninstalling quick...'
%postun
echo 'Success to uninstall quick!'
%prep
%setup -q
%install
install -d %{buildroot}/usr/share/quick
install -d %{buildroot}/usr/share/node-v10.6.0
install -d %{buildroot}/etc/httpd/conf.d
install -d %{buildroot}/usr/bin
install -d %{buildroot}/usr/lib/systemd/system
install -d %{buildroot}/var/www/quick_content
install -d %{buildroot}/var/www/cobbler/misc
install -d %{buildroot}/var/lib/cobbler/kickstarts
install -d %{buildroot}/var/lib/cobbler/snippets
install -d %{buildroot}/var/lib/cobbler/scripts
install -d %{buildroot}/var/log/quick
install -d %{buildroot}/tmp/pippkgs
cp -r ./quick %{buildroot}/usr/share/
cp -r ./extend/node-v10.16.0-linux-x64/* %{buildroot}/usr/share/node-v10.6.0/
cp ./bin/quick.conf %{buildroot}/etc/httpd/conf.d/
cp ./bin/novnc %{buildroot}/usr/bin/
cp ./bin/novnc.service %{buildroot}/usr/lib/systemd/system/
cp ./bin/node.service %{buildroot}/usr/lib/systemd/system/
cp -r ./quick_content %{buildroot}/var/www/
cp -r ./misc/* %{buildroot}/var/www/cobbler/misc/
cp -r ./kickstarts %{buildroot}/var/lib/cobbler/
cp -r ./snippets %{buildroot}/var/lib/cobbler/
cp -r ./scripts %{buildroot}/var/lib/cobbler/
cp -r ./extend/pippkgs %{buildroot}/tmp/

%files
%attr(0755,root,root) /usr/bin/novnc
%config(noreplace) %{apache_etc}/conf.d/quick.conf
/usr/share/quick
/var/www/quick_content
/usr/lib/systemd/system
/var/www/cobbler/misc
/var/lib/cobbler
/var/log/quick
/tmp/pippkgs
/usr/share/node-v10.6.0
%changelog
* Sun Jul 26 2020 osoulmate <askqingya@163.com>
- Quick 1.0.2-1 release
