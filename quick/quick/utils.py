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
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect, SmartConnectNoSSL
import argparse
import atexit
import getpass
import ssl

from quick.models import *
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
class Esxi(object):
    def __init__(self,obj,delimit='  '):
        self.esxi_obj = obj
        self.delimit = delimit
    def gather(self):
        result = {}
        for esxi in self.esxi_obj:
            sn = []
            for i in esxi.summary.hardware.otherIdentifyingInfo:
                if isinstance(i, vim.host.SystemIdentificationInfo):
                    sn.append(i.identifierValue)
            result['spec']     = str(esxi.summary.hardware.numCpuPkgs) + "C" + str(esxi.summary.hardware.numCpuCores) + "核  " + str(esxi.summary.hardware.memorySize/1024/1024) +"MB"
            result['cpuutil']      = '%.3f%%' % (float(esxi.summary.quickStats.overallCpuUsage) /(float(esxi.summary.hardware.numCpuPkgs * esxi.summary.hardware.numCpuCores * esxi.summary.hardware.cpuMhz)) *100)
            result['memoryutil']   = '%.3f%%' % ((float(esxi.summary.quickStats.overallMemoryUsage)/ (float(esxi.summary.hardware.memorySize/1024/1024))) *100)
            result['cputhreads']   = esxi.summary.hardware.numCpuThreads
            result['cpumhz']       = esxi.summary.hardware.cpuMhz
            result['cpumodel']     = esxi.summary.hardware.cpuModel
            result['os']     = esxi.summary.config.product.fullName
            result['vendor']       = esxi.summary.hardware.vendor
            result['model']        = esxi.summary.hardware.model
            result['sn']        = sn
            s = ''
            for ds in esxi.datastore:
                total_size = str(int((ds.summary.capacity)/1024/1024/1024)) + "GB"
                free_size = str(int((ds.summary.freeSpace)/1024/1024/1024)) + "GB"
                filesystem_type = ds.summary.type
                s += "%s[total:%s,free:%s,fs:%s]  "%(ds.name,total_size,free_size,filesystem_type)
            result['storage'] = s
            s = []
            for nt in esxi.network:
                s.append(nt.name)
            result['network'] = s
            vms = []
            for vm in esxi.vm:
                v = {}
                v['name']   =vm.name
                v['powerstatus']  = vm.runtime.powerState
                v['spec']  = str(vm.config.hardware.numCPU) +"C " + str(vm.config.hardware.memoryMB) +'MB'
                v['os']  = vm.config.guestFullName
                if vm.guest.ipAddress:
                    v['ip'] = vm.guest.ipAddress
                else:
                    v['ip'] = 'no vmtools'
                disks = ''
                for d in vm.config.hardware.device:
                    if isinstance(d, vim.vm.device.VirtualDisk):
                        disk_name = d.deviceInfo.label.replace(r" ","")
                        disk_size = str((d.capacityInKB)/1024/1024) + 'GB'
                        disks += "%s  %s"%(disk_name,disk_size)
                v['disk'] = disks
                vms.append(v)
            result['vms'] = vms
        return result

def get_obj(content, vimtype, name=None):
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    obj = [ view for view in container.view]
    return obj

def generate_ip_list(ips,**kw):
    logger = Logger()
    ip_list = []
    ips = ips.split('\n')
    for ip in ips:
        ip = ip.replace('\r','').strip()
        if not is_valid_ip(ip):
            logger.error('%s 不是有效的IP地址'%ip)
        ip_list.append(ip)
    return ip_list
def generate_ip_mask_gateway_mac(obj=None):
    if obj:
        data = []
        newobj = obj.strip().split('\n')
        ip=''
        netmask=''
        gateway=''
        mac=''
        ipmi_ip=''
        ipmi_netmask=''
        ipmi_gateway=''
        ipmi_user=''
        ipmi_pwd=''
        for i in newobj:
            if len(re.split('\s+',i.strip()))==4:
                ip = re.split('\s+',i.strip())[0]
                netmask = re.split('\s+',i.strip())[1]
                gateway = re.split('\s+',i.strip())[2]
                mac = re.split('\s+',i.strip())[3]
            elif len(re.split('\s+',i.strip()))==7:
                ip = re.split('\s+',i.strip())[0]
                netmask = re.split('\s+',i.strip())[1]
                gateway = re.split('\s+',i.strip())[2]
                mac = re.split('\s+',i.strip())[3]
                ipmi_ip = re.split('\s+',i.strip())[4]
                ipmi_netmask = re.split('\s+',i.strip())[5]
                ipmi_gateway = re.split('\s+',i.strip())[6]
            elif len(re.split('\s+',i.strip()))==9:
                ip = re.split('\s+',i.strip())[0]
                netmask = re.split('\s+',i.strip())[1]
                gateway = re.split('\s+',i.strip())[2]
                mac = re.split('\s+',i.strip())[3]
                ipmi_ip = re.split('\s+',i.strip())[4]
                ipmi_netmask = re.split('\s+',i.strip())[5]
                ipmi_gateway = re.split('\s+',i.strip())[6]
                ipmi_user = re.split('\s+',i.strip())[7]
                ipmi_pwd = re.split('\s+',i.strip())[8]
            else:
                pass
            data.append([ip,netmask,gateway,mac,ipmi_ip,ipmi_netmask,ipmi_gateway,ipmi_user,ipmi_pwd])
        return data

def generate_data(osip,task_name,profile_name,progress,owner):
    logger = Logger()
    data = generate_ip_mask_gateway_mac(osip)
    logger.info(data)
    j=len(data)
    i=0
    for ip,netmask,gateway,mac,ipmi_ip,ipmi_netmask,ipmi_gateway,ipmi_user,ipmi_pwd in data:
        logger.info("%s %s %s %s %s %s %s %s %s "%(ip,netmask,gateway,mac,ipmi_ip,ipmi_netmask,ipmi_gateway,ipmi_user,ipmi_pwd))
        hardware_model = ''
        hardware_sn    = ''
        vendor         = ''
        try:
            ip=ip.strip()
            mac=mac.lower().strip()
            report = Report.objects.filter(ip=ip,bootmac=mac)
            logger.info("%s"%report)
            if report:
                report = report[0]
                hardware_model = report.hardware_model
                hardware_sn    = report.hardware_sn
                vendor         = report.vendor
            subtask = Detail(name=task_name,ip=ip,mac=mac,netmask=netmask,gateway=gateway,ipmi_ip=ipmi_ip,ipmi_netmask=ipmi_netmask,ipmi_gateway=ipmi_gateway,ipmi_user=ipmi_user,ipmi_pwd=ipmi_pwd,vendor=vendor,hardware_model=hardware_model,hardware_sn=hardware_sn,apply_template=profile_name,start_time='0',usetime='0',status=progress,owner=owner,flag='detail')
            subtask.save()
            i=i+1
            task = List.objects.get(name=task_name)
            if i == j:
                task.status = '等待执行'
            else:
                task.status = '初始化(%s/%s)'%(i,j)
            task.save()
        except Exception,e:
            logger.error(str(e))
    return True
def __add_host(ip,user,pwd):
    logger = Logger()
    logger.info("Begin to add host(%s)"%ip)
    try:
        if hasattr(ssl, '_create_unverified_context'):
            context = ssl._create_unverified_context()
        si = SmartConnect(
                host=ip,
                user=user,
                pwd=pwd,
                port=443,
                sslContext=context)
        # disconnect this thing
        atexit.register(Disconnect, si)
        content = si.RetrieveContent()
        esxi_obj = get_obj(content, [vim.HostSystem])
        my_esxi = Esxi(esxi_obj)
        esxi_info = my_esxi.gather()
        esxi_fields = [f for f in Esxi_host._meta.fields]
        kw = {}
        for field in esxi_fields:
            if field.name == 'ip':
                continue
            kw[field.name] = esxi_info[field.name]
        esxi = Esxi_host.objects.get(ip=ip)
        for k,v in kw.items():
            setattr(esxi, k , v)
        esxi.save()
        virt_fields = [f for f in Vm_host._meta.fields]

        for vm in esxi_info['vms']:
            kw = {}
            for field in virt_fields:
                if field.name == 'ip':
                    kw[field.name] = vm['ip']
                elif field.name == 'esxi_ip':
                    kw['esxi_ip'] = ip
                else:
                    kw[field.name] = vm[field.name]
            vm_host= Vm_host(**kw)
            vm_host.save()
        logger.info("End to add host(%s)"%ip)
        return True
    except Exception,e:
        esxi_fields = [f for f in Esxi_host._meta.fields]
        kw = {}
        for field in esxi_fields:
            if field.name == 'ip':
                continue
            kw[field.name] = "获取失败"
        esxi = Esxi_host.objects.get(ip=ip)
        for k,v in kw.items():
            setattr(esxi, k , v)
        esxi.save()
        logger.error("Host(%s) occur error(%s)"%(ip,str(e)))
        return False
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
        try:
            sftp = ssh.open_sftp()
            sftp.put(local_path, target_path)
        except Exception,err:
            logger.error("Host(%s) occur error(%s) in uploading script"%(ip,str(err)))
            return True
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
        if not validate_ip(ip):
            logger.error("(%s) 不是有效格式的IP地址"%ip)
            task = List.objects.get(name=name)
            task.status = "IP格式错误!"
            task.usetime = '0'
            task.start_time = '0'
            task.save()
        subtask = Detail(name=name,ip=ip,mac='unknown',
            hardware_model='unknown',hardware_sn='unknown',ipmi_ip='N/R',
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
                    if len(hardware_model) > 50:
                        hardware_model = hardware_model[-50]
                    if len(sn) > 150:
                        hardware_model = hardware_model[-150]
                    if len(product_name) > 50:
                        product_name = product_name[-50]
                    subtask.mac            = mac
                    subtask.hardware_model = product_name
                    subtask.hardware_sn    = sn
                    subtask.status         = 'ready'
                    subtask.apply_template = apply_template
                    subtask.ipmi_ip        = 'N/R'
                    subtask.owner          = obj.owner
                    subtask.save()
            else:
                subtask = Detail(name=name,ip=ip,mac=mac,vendor=vendor,
                    hardware_model=product_name,hardware_sn=sn,apply_template=apply_template,ipmi_ip='N/R',
                    start_time='0',usetime='0',status='ready',owner=obj.owner,flag='detail')
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
def __quick_batch_exec(name,ip,user,pwd,cmd,is_script,owner,shell):
    if is_script == 'yes':
        cmd_info = 'script(%s)'%cmd[0]
    else:
        cmd_info = 'command(%s)'%cmd
    logger = Logger()
    logger.info("Host(%s) begin to exec %s"%(ip,cmd_info))
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        ssh.connect(ip,22,user,pwd,timeout=15)
    except Exception,e:
        logger.error("To ssh host(%s) use username(%s) and password(%s) in port 22 failure!"%(ip,user,pwd))
        batch_temp = Batch_Temp(name=name,ip=ip,status='failure',result=str(e),owner=owner)
        batch_temp.save()
        logger.info("Host(%s) end to exec %s!"%(ip,cmd_info))
    else:
        if is_script == 'yes':
            try:
                filename = '/var/www/quick_content/temp/batch_script'
                f = open(filename,'w')
                f.write(cmd[1])
                f.close()
                local_path = filename
                target_path = '/tmp/batch_script'
                sftp = ssh.open_sftp()
                sftp.put(local_path, target_path)
                cmd = "sudo %s %s"%(shell,target_path)
                stdin, stdout, stderr = ssh.exec_command(cmd,bufsize=1,timeout=15,get_pty=False,environment=None)
                strdata = stdout.read()
                stderr  = stderr.read()
                if stderr != '':
                    logger.error("Host(%s) occur error(%s) in executing script!"%(ip,stderr))
                    e = stderr
                    status = 'failure'
                else:
                    logger.info("Host(%s) exec %s success!"%(ip,cmd_info))
                    e = strdata
                    status = 'success'
            except Exception,err:
                logger.error("Host(%s) occur error(%s) in executing script!"%(ip,str(err)))
                status = 'failure'
                e = err
            batch_temp = Batch_Temp(name=name,ip=ip,status=str(status),result=str(e),owner=owner)
            batch_temp.save()
            ssh.close()
            logger.info("Host(%s) end to execute %s!"%(ip,cmd_info))
            return True
        else:
            try:
                stdin, stdout, stderr = ssh.exec_command(cmd,bufsize=1,timeout=15,get_pty=False,environment=None)
                strdata = stdout.read()
                stderr  = stderr.read()
                if stderr != '':
                    logger.error("Host(%s) occur error (%s) in executing (%s)!"%(ip,stderr,cmd_info))
                    e = stderr
                    status = 'failure'
                else:
                    logger.info("Host(%s) execute %s success!"%(ip,cmd_info))
                    e = strdata
                    status = 'success'
            except Exception,err:
                logger.error("Host(%s) occur error(%s) in executing (%s)!"%(ip,str(err),cmd_info))
                status = 'failure'
                e = err
            batch_temp = Batch_Temp(name=name,ip=ip,status=str(status),result=str(e),owner=owner)
            batch_temp.save()
            ssh.close()
            logger.info("Host(%s) end to exec %s!"%(ip,cmd_info))
            return True
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

def background_exec(name):
    def runner(self):
        self.logger.info("i am in background_exec(%s)"%name)
        return __background_exec(name)
    return __start_task(runner,name)
def background_add_host(name):
    def runner(self):
        self.logger.info("i am in background_add_host(%s)"%name)
        return __background_add_host(name)
    return __start_task(runner,name)

def __background_add_host(name):
    tasks = Esxi_conn.objects.filter(ip=name)
    gevent_list = []
    if tasks:
        task = tasks[0]
        gevent_list.append(gevent.spawn(__add_host,task.ip,task.username,task.password))
        gevent.joinall(gevent_list)
        return True

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
def __background_exec(name):
    try:
        logger = Logger()
        batch = Batch.objects.filter(name=name)
        logger.info("Batch (%s) in __background_exec"%name)
        gevent_list = []
        if batch:
            batch = batch[0]
            if batch.is_ip == 'no':
                host_group = Host_Group.objects.filter(name=batch.ip_name)
                if host_group:
                    iplist = (host_group[0].content).split('\r\n')
                    ip_list = iplist
                    logger.info("Batch (%s) iplist(%s)"%(name,iplist))
            else:
                iplist = batch.ip_name
                ip_list = generate_ip_list(iplist)
            if batch.is_script == 'yes':
                script = Script.objects.filter(name=batch.script_name)
                if script:
                    cmd = [batch.script_name,script[0].content]
                    if script[0].lang.lower() == "shell":
                        shell = 'sh'
                    elif script[0].lang.lower() == "python":
                        shell = 'python'
                else:
                    return False
            else:
                cmd = batch.script_name
                shell = 'sh'
            for ip in ip_list:
                gevent_list.append(gevent.spawn(__quick_batch_exec,name,ip.strip(),batch.osuser,batch.ospwd,cmd,batch.is_script,batch.owner,shell))
            gevent.joinall(gevent_list)
    except Exception,e:
        logger.error("Batch (%s) occur error(%s)!"%(name,str(err)))
        return False
    else:
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
        except Exception,e:
            self.logger.info("End thread(%s)"%self._run)
            self.logger.error("End task(%s) exit(%s)!"%(self.name,str(e)))
            return False
def add_vnc_token(ip_list,path='/usr/share/quick/extend/novnc/vnc_tokens',token='token',port='5901'):
    for ip in ip_list:
        f = open(path,'a')
        s = "\n"+"sys-"+ip+": "+ip+":"+port
        f.writelines(s)
        f.close()
def add_cobbler_system(remote,token,taskname,ospart,ospackages,raid,bios):
    task_details = Detail.objects.filter(name=taskname)
    for task_detail in task_details:
        ifdatas=[]
        ifeth={'static-eth0':'true',
                'ip_address-eth0':task_detail.ip,
                'netmask-eth0':task_detail.netmask,
                'mac_address-eth0':task_detail.mac}
        ifdatas=[ifeth]
        obj_name='sys-%s'%task_detail.ip
        profile=task_detail.apply_template
        gateway=task_detail.gateway
        ks_meta='partition=%s package=%s raid=%s bios=%s'%(ospart,ospackages,raid,bios)
        fields=[{'name':'name','value':obj_name},
                {'name':'profile','value':profile},
                {'name':'ks_meta','value':ks_meta},
                {'name':'gateway','value':gateway}]
        try:
            if not remote.has_item('system', obj_name):
                obj_id = remote.new_item('system', token )
            else:
                remote.xapi_object_edit('system', obj_name, "remove", {'name': obj_name, 'recursive': True}, token)
                obj_id = remote.new_item('system', token)
            for field in fields:
                remote.modify_item('system',obj_id,field['name'],field['value'],token)
            for ifdata in ifdatas:
                remote.modify_system(obj_id, 'modify_interface', ifdata,token)
        except Exception,e:
            task_detail.status=e
            task_detail.save()
            continue
        else:
            remote.save_item('system', obj_id,token,'new')
            task_detail.status='ready'
            task_detail.save()
    return True

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

def is_valid_ip(strdata=None):
    if not strdata:
        return False
    else:
        if re.match(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$",strdata):
            return True
        else:
            return False

def validate_ip(strdata=None):
    ippattern = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")
    if not ippattern.match(strdata):
        return False
    iparray = strdata.split(".");
    ip1 = int(iparray[0])
    ip2 = int(iparray[1])
    ip3 = int(iparray[2])
    ip4 = int(iparray[3])
    if ip1<0 or ip1>255 or ip2<0 or ip2>255 or ip3<0 or ip3>255 or ip4<0 or ip4>255:
       return False
    return True







