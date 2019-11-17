#!/usr/bin/env python
#-*- coding=utf-8 -*-
from __future__ import print_function
import paramiko
import glob
import os
import gevent
from threading import Thread
import re
import time
from quick.models import List,Detail
ERROR       = "ERROR"
WARNING     = "WARNING"
DEBUG       = "DEBUG"
INFO        = "INFO"

class Logger(object):
    def __init__(self, logfile="/var/log/quick/quick.log"):
        self.logfile = None
        # Main logfile is append mode, other logfiles not.
        if not os.path.exists(os.path.dirname(logfile)):
            try:
                os.mkdir("/var/log/quick")
            except IOError:
                return
        if not os.path.exists(logfile) and os.path.exists(os.path.dirname(logfile)):
            self.logfile = open(logfile, "a")
            self.logfile.close()
        try:
            self.logfile = open(logfile, "a")
        except IOError:
            # You likely don't have write access, this logger will just print 
            # things to stdout.
            pass
    def warning(self, msg):
        self.__write(WARNING, msg)

    def error(self, msg):
        self.__write(ERROR, msg)

    def debug(self, msg):
        self.__write(DEBUG, msg)

    def info(self, msg):
        self.__write(INFO, msg)

    def flat(self, msg):
        self.__write(None, msg)

    def __write(self, level, msg):
    
        if level is not None:
            msg = "%s - %s | %s" % (time.asctime(), level, msg)

        if self.logfile is not None:
            self.logfile.write(msg)
            self.logfile.write("\n")
            self.logfile.flush()
        else:
            print(msg)
    def handle(self):
        return self.logfile
    def close(self):
        self.logfile.close()

def generate_ip_list(ip,**kw):
    ip_list = []
    if ',' in ip:
        new_ip_list = ip.split(',')
        for ip in new_ip_list:
            if '-' in ip:
                start_ip = ip.split('-')[0]
                end_ip = ip.split('-')[1]
                ip_prefix = start_ip.split('.')[0]+'.'+start_ip.split('.')[1]+'.'+start_ip.split('.')[2]
                ip_range = range(int(start_ip.split('.')[3]),int(end_ip.split('.')[3])+1)
                for ip_postfix in ip_range:
                    ip_list.append(ip_prefix+'.'+str(ip_postfix))
            else:
                ip_list.append(ip)
    elif '-' in ip:
        start_ip = ip.split('-')[0]
        end_ip = ip.split('-')[1]
        ip_prefix = start_ip.split('.')[0]+'.'+start_ip.split('.')[1]+'.'+start_ip.split('.')[2]
        ip_range = range(int(start_ip.split('.')[3]),int(end_ip.split('.')[3])+1)
        for ip_postfix in ip_range:
            ip_list.append(ip_prefix+'.'+str(ip_postfix))
    else:
        ip_list.append(ip) 
    return ip_list
def generate_ip_mask_gateway_mac(obj=None):
    if obj:
        data = []
        newobj = obj.strip().split('\n')
        for i in newobj:
            if len(re.split('\s+',i.strip()))>4:
                ip = re.split('\s+',i.strip())[0]
                netmask = re.split('\s+',i.strip())[1]
                gateway = re.split('\s+',i.strip())[2]
                mac1 = re.split('\s+',i.strip())[3]
                mac2 = re.split('\s+',i.strip())[4]
                mac=mac1+','+mac2
            elif len(re.split('\s+',i.strip()))==4:
                ip = re.split('\s+',i.strip())[0]
                netmask = re.split('\s+',i.strip())[1]
                gateway = re.split('\s+',i.strip())[2]
                mac = re.split('\s+',i.strip())[3]
            data.append([ip,netmask,gateway,mac])
        return data

def generate_data(osip,task_name,profilename,usetime,progress,owner):
    data = generate_ip_mask_gateway_mac(osip)
    j=len(data)
    i=0
    for ip,mask,gateway,mac in data:
        subtask = Detail(name=task_name,ip=ip,mac=mac,hardware_model='wait',netmask=mask,gateway=gateway,
                                ipmi_ip='wait',hardware_sn='wait',apply_template=profilename,start_time='0',
                                usetime='0',status=progress,owner=owner,flag='detail')
        subtask.save()
        i=i+1
        task = List.objects.get(name=task_name)
        if i == j:
            task.status = '等待执行'
        else:
            task.status = '初始化(%s/%s)'%(i,j)
        task.save()
    return True

def __quick_install_os(name,ip,obj,ip_list):
    logger = Logger()
    logger.info("Begin to configure host(%s) before to reinstall..."%ip)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip,22,obj.osuser,obj.ospwd,timeout=10)
    except:
        ssh.close()
        return False
    else:
        py2in, py2out, py2err = ssh.exec_command("hash python2",bufsize=1,timeout=None,get_pty=False,environment=None)
        is_suse_cmd="if [ -e /etc/SuSE-release ];then echo 'suse';else echo 'none';fi"
        is_suse_in,is_suse_out,is_suse_err = ssh.exec_command(is_suse_cmd)
        py2err = py2err.read()
        is_suse_out = is_suse_out.read()
        if py2err:
            py = "python3"
            use_shell = "qios3.py"
        else:
            py = "python2"
            use_shell = "qios2.py"
        if 'suse' in is_suse_out:
            use_para = " -r -k "
        else:
            use_para = " -r "
        local_path = '/usr/share/quick/agent/%s'%use_shell
        target_path = '/tmp/qios'
        sftp = ssh.open_sftp()
        sftp.put(local_path, target_path)
        if 'ubuntu' in obj.osrelease.lower():
            use_para += ' --embed'
        cmd = "sudo %s /tmp/qios --release='%s' --vncpassword='hellovnc' --sshpassword='hellossh' %s --reboot --report"%(py,obj.osrelease,use_para)
        logger.info("on host(%s) execute command(%s) "%(ip,cmd))
        try:
            stdin, stdout, stderr = ssh.exec_command(cmd,bufsize=1,timeout=15,get_pty=True,environment=None)
            strdata = stdout.read()
            if not strdata:
                logger.info("host(%s) report('') "%ip)
                logger.info("End to configure host(%s),now is reload new kernel..."%ip)
            else:
                logger.info("host(%s) report(%s) "%(ip,strdata))
                logger.info("End to configure host(%s),now is rebooting..."%ip)
        except Exception,err:
            if 'suse' in is_suse_out:
                logger.info("host(%s) report(run kexec -e to loaded) "%ip)
                logger.info("End to configure host(%s),now is reload new kernel..."%ip)
            else:
                logger.info("host(%s) connect timeout(%s) "%(ip,err))
        return True
def __get_host_info(name,ip,user,pwd,obj,iplist):
    logger = Logger()
    logger.info("Begin to collect host(%s) info(vendor,mac,sn...)"%ip)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    apply_template="%s-%s"%(obj.osrelease,obj.osarch)
    try:
        ssh.connect(ip,22,user,pwd,timeout=15)
    except:
        logger.error("ssh host(%s) use username(%s) and password(%s) in port 22 failure !"%(ip,user,pwd))
        subtask = Detail(name=name,ip=ip,mac='unknown',
            hardware_model='unknown',hardware_sn='unknown',
            apply_template=apply_template,start_time='0',usetime='0',
            status='ssh connect failure',owner=obj.owner,flag='detail')
        subtask.save()
        successed = len(Detail.objects.filter(name=name))
        if len(iplist) == successed:
            status = '等待执行...'
        else:
            status = '任务初始化(%d/%d)'%(successed,len(iplist))
        task = List.objects.get(name=name)
        task.status = status
        task.save()
        ssh.close()
        logger.info("End to collect Host(%s) info(vendor,mac,sn...)"%ip)
    else:
        ip_addr_cmd = 'sudo /sbin/ip addr'
        stdin, stdout, stderr = ssh.exec_command(ip_addr_cmd,bufsize=1,timeout=None,get_pty=True,environment=None)
        strdata = stdout.read()
        stderr  = stderr.read()
        if stderr != '':
            logger.info("Host(%s) error in exec_command(ip_addr_cmd) %s"%(ip,stderr))
        if 'bond' in strdata:
            bond_mac_cmd = 'cat /proc/net/bonding/bond0'
            stdin, stdout, stderr = ssh.exec_command(bond_mac_cmd,bufsize=1,timeout=None,get_pty=True,environment=None)
            mac_data = stdout.read()
            stderr  = stderr.read()
            if stderr != '':
                logger.error("Host(%s) error in exec_command(bond_mac_cmd) %s"%(ip,stderr))
            mac = re.findall(r'\s+([a-f0-9]{2}:[a-f0-9]{2}:[a-f0-9]{2}:[a-f0-9]{2}:[a-f:0-9]{2}:[a-f:0-9]{2})\s+', mac_data.lower())
        else:
            mac=re.findall(r'\s+link/ether\s+([a-f0-9]{2}:[a-f0-9]{2}:[a-f0-9]{2}:[a-f0-9]{2}:[a-f:0-9]{2}:[a-f:0-9]{2})\s+', strdata.lower())
        mac = ','.join(mac)
        logger.info("Host(%s) mac is %s"%(ip,mac))
        #ipmiip_cmd = 'ipmitool lan print'
        gather_vendor_cmd = 'sudo /usr/sbin/dmidecode -s system-manufacturer'
        gather_product_name_cmd = 'sudo /usr/sbin/dmidecode -s system-product-name'
        gather_sn_cmd = 'sudo /usr/sbin/dmidecode -s system-serial-number'
        stdin, stdout, stderr = ssh.exec_command(gather_vendor_cmd,bufsize=1,timeout=None,get_pty=True,environment=None)
        vendor = stdout.read()
        stderr  = stderr.read()
        if stderr !='':
            logger.error("Host(%s) error in exec_command(gather_vendor_cmd) %s"%(ip,stderr))
        else:
            logger.info("Host(%s) vendor is %s"%(ip,vendor))
        stdin, stdout, stderr = ssh.exec_command(gather_product_name_cmd,bufsize=1,timeout=None,get_pty=True,environment=None)
        product_name = stdout.read()
        stderr  = stderr.read()
        if stderr !='':
            logger.info("Host(%s) error in exec_command(gather_product_name_cmd) %s"%(ip,stderr))
        else:
            logger.info("Host(%s) product_name is %s"%(ip,product_name))
        stdin, stdout, stderr = ssh.exec_command(gather_sn_cmd,bufsize=1,timeout=None,get_pty=True,environment=None)
        sn = stdout.read()
        stderr  = stderr.read()
        if stderr !='':
            logger.info("Host(%s) error in exec_command(gather_sn_cmd) %s"%(ip,stderr))
        else:
            logger.info("Host(%s) sn is %s"%(ip,sn))
        try:
            """
            when task first execute is not fully collecting all hosts and  execute again,
            """
            subtasks = Detail.objects.filter(name=name,ip=ip)
            if subtasks:
                for subtask in subtasks:
                    subtask.mac            = mac
                    subtask.hardware_model = product_name
                    subtask.hardware_sn    = sn
                    subtask.status         = '就绪'
                    subtask.apply_template = apply_template
                    subtask.owner          = obj.owner
                    subtask.save()
            else:
                subtask = Detail(name=name,ip=ip,mac=mac,vendor=vendor,
                    hardware_model=product_name,hardware_sn=sn,apply_template=apply_template,
                    start_time='0',usetime='0',status='就绪',owner=obj.owner,flag='detail')
                subtask.save()
            successed = len(Detail.objects.filter(name=name))
            if len(iplist) == successed:
                status = '等待执行...'
            else:
                status = '任务初始化(%d/%d)'%(successed,len(iplist))
            task = List.objects.get(name=name)
            task.status = status
            task.save()
            ssh.close()
        except Exception,err:
            logger.eror(err)
        logger.info("End to collect Host(%s) info(vendor,mac,sn...)"%ip)
def __start_task(thr_obj_fn,name):
    logger = Logger()
    logger.info("Start task(%s)"%name)
    thr_obj = QuickThread(name,logger)
    thr_obj._run = thr_obj_fn
    logger.info("Start thread(%s)"%thr_obj._run)
    thr_obj.start()
    return True
def background_collect(name):
    def runner(self):
        self.logger.info("i am in background_collect(%s)"%name)
        try:
            rc = __background_collect(name)
        except Exception,err:
            self.logger.error(err)
        else:
            return True 
    return __start_task(runner,name)
def background_qios(name):
    def runner(self):
        self.logger.info("i am in background_qios(%s)"%name)
        return __background_qios(name)
    return __start_task(runner,name)
def __background_collect(name):
    tasks = List.objects.filter(name=name)
    gevent_list = []
    if tasks:
        task = tasks[0]
        ip_list = generate_ip_list(task.ips)
        for ip in ip_list:
            gevent_list.append(gevent.spawn(__get_host_info,name,ip,task.osuser,task.ospwd,task,ip_list))
        gevent.joinall(gevent_list)
        return True
def __background_qios(name):
    tasks = List.objects.filter(name=name)
    gevent_list = []
    if tasks:
        task = tasks[0]
        ip_list = generate_ip_list(task.ips)
        for ip in ip_list:
            gevent_list.append(gevent.spawn(__quick_install_os,name,ip,task,ip_list))
        gevent.joinall(gevent_list)
        return True
class QuickThread(Thread):
    def __init__(self,name,logger):
        Thread.__init__(self)
        self.name            = name
        self.logger          = logger
    def run(self):
        time.sleep(1)
        try:
            rc = self._run(self)
            self.logger.info("End thread(%s)"%self._run)
            self.logger.info("End task(%s)"%self.name)
            return rc
        except:
            return False
def add_vnc_token(ip_list,path='/usr/share/quick/extend/novnc/vnc_tokens',token='token',port='5901'):
    for ip in ip_list:
        f = open(path,'a')
        s = "\n"+"sys-"+ip+": "+ip+":"+port
        f.writelines(s)
        f.close()
def add_cobbler_system(remote,token,taskname,ospart,ospackages,raid):
    task_details = Detail.objects.filter(name=taskname)
    for task_detail in task_details:
        ifdatas=[]
        if len(task_detail.mac.split(','))>1:
            mac1=task_detail.mac.split(',')[0]
            mac2=task_detail.mac.split(',')[1]
            ifbond={'static-bond0':'true',
                    'ip_address-bond0':task_detail.ip,
                    'netmask-bond0':task_detail.netmask,
                    'bonding_opts-bond0':'mode=active-backup miimon=100',
                    'interface_type-bond0': 'bond',}
            ifeth0={'static-eth0':'true',
                    'interface_master-eth0':'bond0',
                    'interface_type-eth0': 'bond_slave',
                    'mac_address-eth0':mac1}
            ifeth1={'static-eth1':'true',
                    'interface_master-eth1':'bond0',
                    'interface_type-eth1': 'bond_slave',
                    'mac_address-eth1':mac2}
            ifdatas=[ifbond,ifeth0,ifeth1]
        else:
            ifeth={'static-eth0':'true',
                    'ip_address-eth0':task_detail.ip,
                    'netmask-eth0':task_detail.netmask,
                    'mac_address-eth0':task_detail.mac}
            ifdatas=[ifeth]
        obj_name='sys-%s'%task_detail.ip
        profile=task_detail.apply_template
        gateway=task_detail.gateway
        ks_meta='partition=%s package=%s raid=%s'%(ospart,ospackages,raid)
        fields=[{'name':'name','value':obj_name},
                {'name':'profile','value':profile},
                {'name':'ks_meta','value':ks_meta},
                {'name':'gateway','value':gateway}]
        if not remote.has_item('system', obj_name):
            obj_id = remote.new_item('system', token )
        else:
            try:
                remote.xapi_object_edit('system', obj_name, "remove", {'name': obj_name, 'recursive': True}, token)
            except Exception, e:
                pass
            else:
                obj_id = remote.new_item('system', token )
        for field in fields:
            try:
                remote.modify_item('system',obj_id,field['name'],field['value'],token)
            except Exception, e:
                task_detail.status=e
                task_detail.save()
        for ifdata in ifdatas:
            try:
                remote.modify_system(obj_id, 'modify_interface', ifdata,token)
            except Exception, e:
                task_detail.status=e
                task_detail.save()
        try:
            remote.save_item('system', obj_id,token,'new')
            task_detail.status='initializing...'
            task_detail.save()
            return True
        except Exception, e:
            task_detail.status=e
            task_detail.save()
            return False

def timers(diff=None):
    if diff > 60 and diff < 3600:
        minite = diff / 60
        second = diff % 60
        diff = '%d分%d秒'%(minite,second)
    elif diff >= 3600:
        hour = diff / 3600
        minite = diff % 3600 / 60
        second = diff % 3600 % 60 
        diff = "%d小时%d分%d秒" %(hour,minite,second)
    else:
        diff = '%d秒'%diff
    return diff