#!/usr/bin/env python
#-*- coding=utf-8 -*-
"""
qios = quickly install os

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
 
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
 
You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
02110-1301  USA
"""

QUICK_SERVER = '192.168.31.120'
QUICK_USER   = 'cobbler'
QUICK_PASS   = 'cobbler'
import os
import traceback
import shlex
import tempfile
ANCIENT_PYTHON = 0
try:
    try:
        from optparse import OptionParser
    except:
        from opt_parse import OptionParser # importing this for backwards compat with 2.2
    try:
        import subprocess as sub_process
    except:
        import sub_process
except:
    # the main "replace-self" codepath of qios must support
    # Python 1.5.  Other sections may use 2.3 features (nothing newer)
    # provided they are conditionally imported.  This is to support
    # EL 2.1. -- mpd
    ANCIENT_PYTHON = 1

import urllib.request, urllib.error, urllib.parse
import time
import shutil
import errno
import re
import sys
import xmlrpc.client
import string
from threading import Thread
"""
qios --release='centos7.3' -r -k
"""


def main():
    """
    Command line stuff...
    """

    try:
        logger = setupLogging("qios")
    except:
        # most likely running RHEL3, where we don't need virt logging anyway
        print("no logger")

    if ANCIENT_PYTHON:
        print("- command line usage on this version of python is unsupported")
        logger.info("command line usage on this version of python is unsupported")
        print("- usage via spacewalk APIs only.  Python x>=2.3 required")
        logger.info("usage via spacewalk APIs only.  Python x>=2.3 required")
        return
    try:
        shutil.rmtree("/var/spool/qios")
    except OSError as xxx_todo_changeme:
        (err, msg) = xxx_todo_changeme.args
        if err != errno.ENOENT:
            raise
    try:
        os.makedirs("/var/spool/qios")
    except OSError as xxx_todo_changeme1:
        (err, msg) = xxx_todo_changeme1.args
        if err != errno.EEXIST:
            raise
    p = OptionParser()
    p.add_option("-S", "--server",
                 dest="server",
                 default=QUICK_SERVER,
                 help="attach to this cobbler server")
    p.add_option("-P", "--port",
                 dest="port",
                 help="cobbler port (default 80)")
    p.add_option("", "--user",
                 dest="username",
                 default=QUICK_USER,
                 help="attach to this cobbler USER")
    p.add_option("", "--password",
                 dest="password",
                 default=QUICK_PASS,
                 help="attach to this cobbler PASSWORD")
    p.add_option("-r", "--replace-self",
                 dest="is_replace",
                 action="store_true",
                 help="reinstall this host at next reboot")
    p.add_option("-k", "--kexec",
                 dest="use_kexec",
                 action="store_true",
                 help="Instead of writing a new bootloader config when using --replace-self, just kexec the new kernel and initrd")
    p.add_option("", "--breed",
                 dest="breed",
                 help="os breed")
    p.add_option("", "--release",
                 dest="release",
                 help="os release")
    p.add_option("", "--arch",
                 dest="arch",
                 default='x86_64',
                 help="os arch")
    p.add_option("", "--add-reinstall-entry",
                 dest="add_reinstall_entry",
                 action="store_true",
                 help="when used with --replace-self, just add entry to grub, do not make it the default")
    p.add_option("-d", "--drive",
                 dest="drive",
                 help="the extra drives that need to load")
    p.add_option("", "--partition",
                 dest="partition",
                 help="the partition of os")
    p.add_option("", "--package",
                 dest="package",
                 help="the extra packages that need to install")
    p.add_option("-m", "--mail",
                 dest="mail",
                 help="notice mail")
    p.add_option("", "--make_raid",
                 dest="make_raid",
                 help="only used for needing to create or rebuilding raid")
    p.add_option("", "--embed",
                 dest="embed_seed",
                 action="store_true",
                 help="When used with  --replace-self, embed the preseed.cfg in the initrd")
    p.add_option("", "--report",
                 dest="report",
                 action="store_true",
                 help="When used with --report,the progress of execution will send to server")
    p.add_option("", "--reboot",
                 dest="reboot",
                 action="store_true",
                 help="When used with --reboot,will reboot after success")
    p.add_option("", "--vncpassword",
                 dest="vncpassword",
                 help="the password for vnc connect in installing")
    p.add_option("", "--sshpassword",
                 dest="sshpassword",
                 help="the password for ssh connect in installing")
    (options, args) = p.parse_args()
    try:
        k = Qios()
        k.server              = options.server
        k.is_replace          = options.is_replace
        k.use_kexec           = options.use_kexec
        k.breed               = options.breed
        k.release             = options.release
        k.arch                = options.arch
        k.drive               = options.drive
        k.partition           = options.partition
        k.package             = options.package
        k.mail                = options.mail
        k.make_raid           = options.make_raid
        k.add_reinstall_entry = options.add_reinstall_entry
        k.embed_seed          = options.embed_seed
        k.report              = options.report
        k.reboot              = options.reboot
        k.vncpassword         = options.vncpassword
        k.sshpassword         = options.sshpassword
        if options.port is not None:
            k.port              = options.port
        if options.server is None:
            raise InfoException("--server is required")
        xmlrpc_server = connect_to_server(server=options.server, port=options.port)
        found = 0
        options_list=[options.is_replace,
                      options.use_kexec, 
                      options.breed, 
                      options.release,
                      options.drive,
                      options.partition,
                      options.make_raid,
                      options.add_reinstall_entry,
                      options.embed_seed,
                      options.package, 
                      options.mail]
        for x in options_list:
            if x:
               found = found+1
        if found > 0:
            partition = options.partition
            package   = options.package
            make_raid = options.make_raid
            mail      = options.mail
            release   = options.release
            arch      = options.arch
            server    = options.server
            report    = options.report
            user      = options.username
            pwd       = options.password
            profile="%s-%s"%(release,arch)
        else:
            user = QUICK_USER
            pwd = QUICK_PASS
            print("*"*54)
            print(" "*54)
            print("Hi,Welcome to use self-reinstall program...")
            print(" "*54)
            print("*"*54)
            print(" "*54)
            print('please choose the os that you want to reinstall...')
            print(" "*54)
            profiles=xmlrpc_server.get_profiles()
            os_release=list()
            for profile in profiles:
                os_release.append(profile['name'])
            os_release.sort()
            total = len(os_release)
            i = 1
            j = 0
            while i<total:
                print("%s.%-20s      %s.%-20s"%(i,os_release[j],i+1,os_release[j+1]))
                i = i+2
                j = j+2
            print(" "*54)
            print("*"*54)
            your_choose=input("your choose: ")
            if your_choose:
                print("you hope to install: %s"% os_release[int(your_choose)-1])
            else:
                return 0
            your_mail=input("your email: ")
            if your_mail:
                mail = your_mail
            else:
                mail = None
            your_ack=input("continue? (y/n) ")
            if your_ack == 'y' or your_ack == 'Y':
                profile = os_release[int(your_choose)-1]
                partition = None
                package   = None
                make_raid = None
                release   = None
                arch      = None
                server    = None
                report    = None
                k.is_replace = True
                if 'ubuntu' in profile:
                    k.embed_seed = True
                if check_dist() in ("suse", "opensuse"):
                    k.use_kexec = True
            else:
                return 0
        ifdatas,hostip,gateway,comment = host_info()
        obj_name='sys-%s'%hostip
        token = xmlrpc_server.login(user,pwd)
        ksmeta='partition=%s package=%s raid=%s mail=%s'%(partition,package,make_raid,mail)
        fields=[{'name':'name','value':obj_name},
                {'name':'profile','value':profile},
                {'name':'ks_meta','value':ksmeta},
                {'name':'comment','value':comment},
                {'name':'gateway','value':gateway}]
        editmode = 'new'
        if not xmlrpc_server.has_item('system', obj_name):
            obj_id = xmlrpc_server.new_item('system', token )
        else:
            try:
                xmlrpc_server.xapi_object_edit('system', obj_name, "remove", {'name': obj_name, 'recursive': True}, token)
            except Exception as e:
                print(str(e))
                logger.error(str(e))
                notice_server(str(e),options.server,options.report)
            else:
                obj_id = xmlrpc_server.new_item('system', token )
        for field in fields:
            try:
                xmlrpc_server.modify_item('system',obj_id,field['name'],field['value'],token)
            except Exception as e:
                print(str(e))
                logger.error(str(e))
                notice_server(str(e),options.server,options.report)
        for ifdata in ifdatas:
            try:
                xmlrpc_server.modify_system(obj_id,'modify_interface',ifdata,token)
            except Exception as e:
                print(str(e))
                logger.error(str(e))
                notice_server(str(e),options.server,options.report)
        try:
            xmlrpc_server.save_item('system', obj_id,token,editmode)
        except Exception as e:
            print(str(e))
            logger.error(str(e))
            notice_server(str(e),options.server,options.report)
        systems=xmlrpc_server.get_systems()
        for system in systems:
            if obj_name == system['name']:
                k.system = obj_name
                break
        if k.system:
            strdata='success to add cobbler system %s'%obj_name
            logger.info(strdata)
            notice_server(strdata,options.server,options.report)
            k.xmlrpc_server = xmlrpc_server 
            k.logger = logger
            k.run()
        else:
            strdata="%s is not exist in server!"%obj_name
            print(strdata)
            logger.info(strdata)
            notice_server(strdata,options.server,options.report)
            return 1
    except Exception as e:
        (xa, xb, tb) = sys.exc_info()
        try:
            getattr(e,"from_quick")
            print(str(e)[1:-1]) # nice exception, no traceback needed
        except:
            print(xa)
            print(xb)
            print(traceback.format_list(traceback.extract_tb(tb)))
        return 1

    return 0
#=======================================================
class Progress:
    def __init__(self):
        self._flag = False
    def timer(self,progress='default'):
        if progress == 'default':
            i = 19
            while self._flag:
                print(" %s \r" % (i * "="),)
                sys.stdout.flush()
                i = (i + 1) % 20
                time.sleep(1)
            print(" %s" % (19 * "="))
        else:
            i = 1
            while self._flag:
                print(" %s \r" % (i * "."),)
                sys.stdout.flush()
                i = i+1
                time.sleep(1)
            print(" %s \r" % (i * "."))
    def start(self):
        self._flag = True
        Thread(target=self.timer,kwargs={"progress":"custom"}).start()
    def stop(self):
        self._flag = False
        time.sleep(1)
#=======================================================
def setupLogging(appname):
    """
    set up logging ... code borrowed/adapted from virt-manager
    """
    import logging
    import logging.handlers

    dateFormat = "%a, %d %b %Y %H:%M:%S"
    fileFormat = "[%(asctime)s " + appname + " %(process)d] %(levelname)s (%(module)s:%(lineno)d) %(message)s"
    streamFormat = "%(asctime)s %(levelname)-8s %(message)s"
    filename = "/var/log/qios.log"

    rootLogger = logging.getLogger()
    rootLogger.setLevel(logging.DEBUG)
    fileHandler = logging.handlers.RotatingFileHandler(filename, "a",
                                                       1024*1024, 5,encoding="utf-8")

    fileHandler.setFormatter(logging.Formatter(fileFormat,dateFormat))
    rootLogger.addHandler(fileHandler)
    """
    streamHandler = logging.StreamHandler(sys.stderr)
    streamHandler.setFormatter(logging.Formatter(streamFormat,
                                                 dateFormat))
    streamHandler.setLevel(logging.DEBUG)
    rootLogger.addHandler(streamHandler)
    """
    return rootLogger

def urlread(url):
    """
    to support more distributions, implement (roughly) some 
    parts of urlread and urlgrab from urlgrabber, in ways that
    are less cool and less efficient.
    """
    print("- reading URL: %s" % url)
    if url is None or url == "":
        raise InfoException("invalid URL: %s" % url)

    elif url[0:3] == "nfs":
        try:
            ndir  = os.path.dirname(url[6:])
            nfile = os.path.basename(url[6:])
            nfsdir = tempfile.mkdtemp(prefix="quick_nfs",dir="/tmp")
            nfsfile = os.path.join(nfsdir,nfile)
            cmd = ["mount","-t","nfs","-o","ro", ndir, nfsdir]
            subprocess_call(cmd)
            fd = open(nfsfile)
            data = fd.read()
            fd.close()
            cmd = ["umount",nfsdir]
            subprocess_call(cmd)
            return data
        except:
            traceback.print_exc()
            raise InfoException("Couldn't mount and read URL: %s" % url)
          
    elif url[0:4] == "http":
        try:
            import urllib.request, urllib.parse, urllib.error
            fd = urllib.request.urlopen(url)
            data = fd.read()
            fd.close()
            return data
        except:
            if ANCIENT_PYTHON:
                # this logic is to support python 1.5 and EL 2
                import urllib.request, urllib.parse, urllib.error
                fd = urllib.request.urlopen(url)
                data = fd.read()
                fd.close()
                return data
            traceback.print_exc()
            raise InfoException("Couldn't download: %s" % url)
    elif url[0:4] == "file":
        try:
            fd = open(url[5:])
            data = fd.read()
            fd.close()
            return data
        except:
            raise InfoException("Couldn't read file from URL: %s" % url)
    else:
        raise InfoException("Unhandled URL protocol: %s" % url)

def urlgrab(url,saveto):
    """
    like urlread, but saves contents to disk.
    see comments for urlread as to why it's this way.
    """
    data = urlread(url)
    fd = open(saveto, "wb+")
    fd.write(data)
    fd.close()

def subprocess_call(cmd,ignore_rc=0):
    """
    Wrapper around subprocess.call(...)
    """
    print("- %s" % cmd)
    if not ANCIENT_PYTHON:
        rc = sub_process.call(cmd)
    else:
        cmd = string.join(cmd, " ")
        print("cmdstr=(%s)" % cmd)
        rc = os.system(cmd)
    if rc != 0 and not ignore_rc:
        raise InfoException("command failed (%s)" % rc)
    return rc

def subprocess_get_response(cmd, ignore_rc=False, get_stderr=False):
    """
    Wrapper around subprocess.check_output(...)
    """
    print("- %s" % cmd)
    rc = 0
    result = ""
    if not ANCIENT_PYTHON:
        if get_stderr:
            p = sub_process.Popen(cmd, stdout=sub_process.PIPE,
                    stderr=sub_process.PIPE)
        else:
            p = sub_process.Popen(cmd, stdout=sub_process.PIPE)
        result, stderr_result = p.communicate()
        rc = p.wait()
    else:
        cmd = string.join(cmd, " ")
        print("cmdstr=(%s)" % cmd)
        rc = os.system(cmd)
    if not ignore_rc and rc != 0:
        raise InfoException("command failed (%s)" % rc)
    if get_stderr:
        return rc, result, stderr_result
    return rc, result

def input_string_or_hash(options,delim=None,allow_multiples=True):
    """
    Older cobbler files stored configurations in a flat way, such that all values for strings.
    Newer versions of cobbler allow dictionaries.  This function is used to allow loading
    of older value formats so new users of cobbler aren't broken in an upgrade.
    """

    if options is None:
        return {}
    elif type(options) == list:
        raise InfoException("No idea what to do with list: %s" % options)
    elif type(options) == type(""):
        new_dict = {}
        #tokens = string.split(options, delim)
        tokens = options.split(delim)
        for t in tokens:
            tokens2 = t.split("=")
            if len(tokens2) == 1:
                # this is a singleton option, no value
                key = tokens2[0]
                value = None
            else:
                key = tokens2[0]
                value = tokens2[1]

            # if we're allowing multiple values for the same key,
            # check to see if this token has already been
            # inserted into the dictionary of values already

            if key in list(new_dict.keys()) and allow_multiples:
                # if so, check to see if there is already a list of values
                # otherwise convert the dictionary value to an array, and add
                # the new value to the end of the list
                if type(new_dict[key]) == list:
                    new_dict[key].append(value)
                else:
                    new_dict[key] = [new_dict[key], value]
            else:
                new_dict[key] = value

        # dict.pop is not avail in 2.2
        if "" in new_dict:
           del new_dict[""]
        return new_dict
    elif type(options) == type({}):
        options.pop('',None)
        return options
    else:
        raise InfoException("invalid input type: %s" % type(options))

def hash_to_string(hash):
    """
    Convert a hash to a printable string.
    used primarily in the kernel options string
    and for some legacy stuff where qios expects strings
    (though this last part should be changed to hashes)
    """
    buffer = ""
    if type(hash) != dict:
       return hash
    for key in hash:
       value = hash[key]
       if value is None:
           buffer = buffer + str(key) + " "
       elif type(value) == list:
           # this value is an array, so we print out every
           # key=value
           for item in value:
              buffer = buffer + str(key) + "=" + str(item) + " "
       else:
              buffer = buffer + str(key) + "=" + str(value) + " "
    return buffer


def check_dist():
    """
    Determines what distro we're running under.  
    """
    os_breed = os.popen("cat /proc/version").read().strip()
    if os.path.exists("/etc/redhat-release") or 'Red' in os_breed:
       return 'redhat'
    elif os.path.exists("/etc/SuSE-release") or 'SUSE' in os_breed:
       return "suse"
    else:
       return "ubuntu"

def os_release():

    """
    This code is borrowed from Cobbler and really shouldn't be repeated.
    """
    if ANCIENT_PYTHON:
        return ("unknown", 0)
    if check_dist() == "redhat":
        fh = open("/etc/redhat-release")
        data = fh.read().lower()
        if data.find("fedora") != -1:
            make = "fedora"
        elif data.find("centos") != -1:
           make = "centos"
        elif data.find("redhat") != -1:
            make = "redhat"
        else:
            make = "redhat"
        release_index = data.find("release")
        rest = data[release_index+7:-1]
        tokens = rest.split(" ")
        for t in tokens:
            try:
                match = re.match('^\d+(?:\.\d+)?', t)
                if match:
                    return (make, float(match.group(0)))
            except ValueError as ve:
                pass
        raise CX("failed to detect local OS version from /etc/redhat-release")
    elif check_dist() == "ubuntu":
        version = sub_process.check_output(("lsb_release","--release","--short")).rstrip()
        make = "ubuntu"
        return (make, float(version))
    elif check_dist() in ("suse", "opensuse"):
        fd = open("/etc/SuSE-release")
        for line in fd.read().split("\n"):
            if line.find("VERSION") != -1:
                version = line.replace("VERSION = ","")
            if line.find("PATCHLEVEL") != -1:
                rest = line.replace("PATCHLEVEL = ","")
        make = "suse"
        return (make, float(version))
    else:
        return ("unknown",0)


def connect_to_server(server=None,port=None):
    if server is None:
        server = os.environ.get("QUICK_SERVER","")
    if server == "":
        raise InfoException("--server must be specified")
    if port is None: 
        port = 80
    connect_ok = 0
    try_urls = [
        "http://%s:%s/cobbler_api" % (server,port),
        "https://%s:%s/cobbler_api" % (server,port),
    ]
    for url in try_urls:
        print("- looking for Cobbler at %s" % url)
        server = __try_connect(url)
        if server is not None:
           return server
    raise InfoException ("Could not find Cobbler.")

def __try_connect(url):
    try:
        xmlrpc_server = xmlrpc.client.Server(url)
        xmlrpc_server.ping()
        return xmlrpc_server
    except:
        traceback.print_exc()
        return None

def len_to_netmask(length=24):
    length=int(length)
    if length<1 or length>32:
        return 'error netmask length!'
    cidr='1'*length+'0'*(32-length)
    netmask=''
    for i in re.findall(r'.{8}',cidr):
        i='0b'+i
        netmask+=str(eval(i))+'.'
    return netmask.strip('.')
def popen(cmd):
    data = os.popen(cmd).read().strip()
    return data
def host_info():
    ifdatas=[]
    if os.path.exists("/proc/net/bonding/bond0"):
        mac = popen("cat /proc/net/bonding/bond0 | grep addr: | awk -F' ' '{print $4}'")
        ip = popen("sudo ip add|grep bond0|grep inet |awk -F' ' '{print $2}'|awk -F'/' '{print $1}'")
        netmask_len = popen("sudo ip add|grep bond0|grep inet |awk -F' ' '{print $2}'|awk -F'/' '{print $2}'")
        ifbond={'static-bond0':'true',
                'ip_address-bond0':ip,
                'netmask-bond0':len_to_netmask(netmask_len),
                'bonding_opts-bond0':'mode=active-backup miimon=100',
                'interface_type-bond0': 'bond'}
        macs=mac.split('\n')
        if len(macs)>1:
            ifeth0={'static-eth0':'true',
                    'interface_master-eth0':'bond0',
                    'interface_type-eth0': 'bond_slave',
                    'mac_address-eth0':macs[0]}
            ifeth1={'static-eth1':'true',
                    'interface_master-eth1':'bond0',
                    'interface_type-eth1': 'bond_slave',
                    'mac_address-eth1':macs[1]}
            ifdatas=[ifbond,ifeth0,ifeth1]
        else:
            ifeth0={'static-eth0':'true',
                    'interface_master-eth0':'bond0',
                    'interface_type-eth0': 'bond_slave',
                    'mac_address-eth0':macs[0]}
            ifdatas=[ifbond,ifeth0]
    else:
        static_interface = 'eth0'
        cmd = r"""
        eth=`sudo ip route|grep default|awk -F' ' '{print $5}'`
        netmask=`sudo ip add|grep $eth|grep inet|awk -F' ' '{print $2}'|awk -F'/' '{print $2}'`
        mac=`sudo ip add|grep -A 2 $eth|grep link/ether|awk -F' ' '{print $2}'`
        ip=`sudo ip add|grep $eth|grep inet|awk -F' ' '{print $2}'|awk -F'/' '{print $1}'`
        printf "%s %s %s" $mac $ip $netmask
        """
        strdata= popen(cmd)
        strdata=strdata.split()
        if len(strdata)==3:
            ip=strdata[1]
            ifeth={'static-eth0':'true',
                  'ip_address-eth0':strdata[1],
                  'netmask-eth0':len_to_netmask(strdata[2]),
                  'mac_address-eth0':strdata[0]}
        else:
            ip=''
            ifeth=[]
        ifdatas=[ifeth]
    gateway=popen("sudo ip route|grep default|awk -F' ' '{print $3}'")
    product_name = popen("sudo /usr/sbin/dmidecode -s system-product-name")
    serial_number = popen("sudo /usr/sbin/dmidecode -s system-serial-number")
    comment={'product_name':product_name, 'sn':serial_number}
    return ifdatas,ip,gateway,comment
def notice_server(strdata,server,report=None):
    if server and report:
        strdata=re.sub('\s+','~',strdata)
        try:
            subprocess_call([
                            'curl',
                            '%s/quick/install/notice/install_%s'%(server,strdata)
                        ])
        except:
            traceback.print_exc()
            return None
#=======================================================

class InfoException(Exception):
    """
    Custom exception for tracking of fatal errors.
    """
    def __init__(self,value,**args):
        self.value = value % args
        self.from_quick = 1
    def __str__(self):
        return repr(self.value)

#=======================================================

class Qios:

    def __init__(self):
        """
        Constructor.  Arguments will be filled in by optparse...
        """
        self.server            = None
        self.port              = None
        self.is_replace        = None
        self.use_kexec         = None
        self.breed             = None
        self.release           = None
        self.partition         = None
        self.package           = None
        self.mail              = None
        self.system            = None
        self.add_reinstall_entry=None
        # This option adds the --copy-default argument to /sbin/grubby
        # which uses the default boot entry in the grub.conf
        # as template for the new entry being added to that file.
        # look at /sbin/grubby --help for more info
        self.no_copy_default   = None
        self.kopts_override    = None
        self.live_cd           = None
        self.xmlrpc_server     = None
        self.logger            = None
        self.report            = None
        self.reboot            = None
        self.vncpassword       = None
        self.sshpassword       = None
    #---------------------------------------------------

    def run(self):
        """
        qios's main function...
        """
        if self.is_replace:
            if self.use_kexec:
                self.kexec_replace()
            else:
                self.replace()
    #---------------------------------------------------

    def safe_load(self,hashv,primary_key,alternate_key=None,default=None):
        if primary_key in hashv: 
            return hashv[primary_key]
        elif alternate_key is not None and alternate_key in hashv:
            return hashv[alternate_key]
        else:
            return default

    #---------------------------------------------------

    def net_install(self,after_download):
        """
        Actually kicks off downloads and auto-ks or virt installs
        """

        # initialise the profile, from the server if any
        if self.system:
            profile_data = self.get_data("system",self.system)
        else:
            profile_data = {}

        if profile_data.get("kickstart","") != "":

            # fix URLs
            if profile_data["kickstart"][0] == "/" or profile_data["template_remote_kickstarts"]:
               if not self.system:
                   profile_data["kickstart"] = "http://%s/cblr/svc/op/ks/profile/%s" % (profile_data['http_server'], profile_data['name'])
               else:
                   profile_data["kickstart"] = "http://%s/cblr/svc/op/ks/system/%s" % (profile_data['http_server'], profile_data['name'])
                
            # If breed is ubuntu/debian we need to source the install tree differently
            # as preseeds are used instead of kickstarts.
            if profile_data["breed"] in [ "ubuntu", "debian", "suse" ]:
                self.get_install_tree_from_profile_data(profile_data)
            else:
                # find install source tree from kernel options
                if not self.get_install_tree_from_kernel_options(profile_data):
                    # Otherwise find kickstart source tree in the kickstart file
                    self.get_install_tree_from_kickstart(profile_data)

            # if we found an install_tree, and we don't have a kernel or initrd
            # use the ones in the install_tree
            if self.safe_load(profile_data,"install_tree"):
                if not self.safe_load(profile_data,"kernel"):
                    profile_data["kernel"] = profile_data["install_tree"] + "/images/pxeboot/vmlinuz"

                if not self.safe_load(profile_data,"initrd"):
                    profile_data["initrd"] = profile_data["install_tree"] + "/images/pxeboot/initrd.img"


        # find the correct file download location 
        if os.path.exists("/boot/efi/EFI/redhat/elilo.conf"):
            # elilo itanium support, may actually still work
            download = "/boot/efi/EFI/redhat"
        else:
            # whew, we have a sane bootloader
            download = "/boot"
        # perform specified action
        if download is not None:
           self.get_distro_files(profile_data, download)
        after_download(self, profile_data)

    #---------------------------------------------------

    def get_install_tree_from_kickstart(self,profile_data):
        """
        Scan the kickstart configuration for either a "url" or "nfs" command
           take the install_tree url from that

        """
        try:
            if profile_data["kickstart"][:4] == "http":
                if not self.system:
                    url_fmt = "http://%s/cblr/svc/op/ks/profile/%s"
                else:
                    url_fmt = "http://%s/cblr/svc/op/ks/system/%s"
                url = url_fmt % (self.server, profile_data['name'])
            else:
                url = profile_data["kickstart"]

            raw = urlread(url)
            lines = raw.splitlines()

            method_re = re.compile('(?P<urlcmd>\s*url\s.*)|(?P<nfscmd>\s*nfs\s.*)')

            url_parser = OptionParser()
            url_parser.add_option("--url", dest="url")
            url_parser.add_option("--proxy", dest="proxy")

            nfs_parser = OptionParser()
            nfs_parser.add_option("--dir", dest="dir")
            nfs_parser.add_option("--server", dest="server")

            for line in lines:
                match = method_re.match(line)
                if match:
                    cmd = match.group("urlcmd")
                    if cmd:
                        (options,args) = url_parser.parse_args(shlex.split(cmd)[1:])
                        profile_data["install_tree"] = options.url
                        break
                    cmd = match.group("nfscmd")
                    if cmd:
                        (options,args) = nfs_parser.parse_args(shlex.split(cmd)[1:])
                        profile_data["install_tree"] = "nfs://%s:%s" % (options.server,options.dir)
                        break

            if self.safe_load(profile_data,"install_tree"):
                print("install_tree:", profile_data["install_tree"])
            else:
                print("warning: kickstart found but no install_tree found")

        except:
            # unstable to download the kickstart, however this might not
            # be an error.  For instance, xen FV installations of non
            # kickstart OS's...
            pass

    #---------------------------------------------------

    def get_install_tree_from_profile_data(self, profile_data):
        """
        Split ks_meta to obtain the tree path. Generate the install_tree
           using the http_server and the tree obtained from splitting ks_meta

        """

        try:
            tree = profile_data["ks_meta"].split()
            # Ensure we only take the tree in case ks_meta args are passed
            # First check for tree= in ks_meta arguments
            meta_re=re.compile('tree=')
            tree_found=''
            for entry in tree:
                if meta_re.match(entry):
                    tree_found=entry.split("=")[-1]
                    break
 
            if tree_found=='':
                # assume tree information as first argument
                tree = tree.split()[0]
            else:
                tree=tree_found
            tree_re = re.compile ('(http|ftp|nfs):')
            # Next check for installation tree on remote server
            if tree_re.match(tree):
                tree = tree.replace("@@http_server@@", profile_data["http_server"])
                profile_data["install_tree"] = tree
            else:
            # Now take the first parameter as the local path
                profile_data["install_tree"] = "http://" + profile_data["http_server"] + tree

            if self.safe_load(profile_data,"install_tree"):
                print("install_tree:", profile_data["install_tree"])
            else:
                print("warning: kickstart found but no install_tree found")
        except:
            pass

    def get_install_tree_from_kernel_options(self, profile_data):
        """
        Split kernel options to obtain the inst.stage2 path. Generate the install_tree
           using the http_server and the tree obtained from the inst.stage2 path

        """

        try:
            tree = profile_data["kernel_options"].split()
            # Ensure we only take the tree in case ks_meta args are passed
            # First check for tree= in ks_meta arguments
            meta_re = re.compile('inst.stage2=')
            tree_found = ''
            for entry in tree:
                if meta_re.match(entry):
                    tree_found = entry.split("=")[-1]
                    break

            if tree_found == '':
                return False
            else:
                tree = tree_found
            tree_re = re.compile('(http|ftp|nfs):')
            # Next check for installation tree on remote server
            if tree_re.match(tree):
                tree = tree.replace(
                    "@@http_server@@",
                    profile_data["http_server"])
                profile_data["install_tree"] = tree
            else:
                # Now take the first parameter as the local path
                profile_data["install_tree"] = "http://" + \
                    profile_data["http_server"] + tree

            if self.safe_load(profile_data, "install_tree"):
                print("install_tree:", profile_data["install_tree"])
            else:
                print("warning: kickstart found but no install_tree found")
        except:
            pass
    #---------------------------------------------------
  
    def kexec_replace(self):
        """
        Prepare to morph existing system by downloading new kernel and initrd
        and preparing kexec to execute them. Allow caller to do final 'kexec
        -e' invocation; this allows modules such as network drivers to be
        unloaded (for cases where an immediate kexec would leave the driver in
        an invalid state.
        """
        def after_download(self, profile_data):
            k_args = self.calc_kernel_args(profile_data)
            kickstart = self.safe_load(profile_data,'kickstart')
            arch      = self.safe_load(profile_data,'arch')
            arch      = arch.encode(encoding='utf-8', errors = 'strict')
            breed     = self.safe_load(profile_data,'breed')
            if breed =='ubuntu':
                if self.embed_seed:
                    progress = Progress()
                    progress.start()
                    self.build_initrd(
                        self.safe_load(profile_data,'initrd_local'),
                        kickstart,
                        profile_data
                    )
                    progress.stop()
            # Validate kernel argument length (limit depends on architecture --
            # see asm-*/setup.h).  For example:
            #   asm-i386/setup.h:#define COMMAND_LINE_SIZE 256
            #   asm-ia64/setup.h:#define COMMAND_LINE_SIZE  512
            #   asm-powerpc/setup.h:#define COMMAND_LINE_SIZE   512
            #   asm-s390/setup.h:#define COMMAND_LINE_SIZE  896
            #   asm-x86_64/setup.h:#define COMMAND_LINE_SIZE    256
            #   arch/x86/include/asm/setup.h:#define COMMAND_LINE_SIZE 2048
            if arch.startswith(b"ppc") or arch.startswith(b"ia64"):
                if len(k_args) > 511:
                    raise InfoException("Kernel options are too long, 512 chars exceeded: %s" % k_args)
            elif arch.startswith(b"s390"):
                if len(k_args) > 895:
                    raise InfoException("Kernel options are too long, 896 chars exceeded: %s" % k_args)
            elif len(k_args) > 2048:
                raise InfoException("Kernel options are too long, 2048 chars exceeded: %s" % k_args)
            if self.vncpassword:
                if len(self.vncpassword)>8 or len(self.vncpassword)<6:
                    strdata = "VNC password must be six to eight characters long"
                    self.logger.error(strdata)
                    notice_server(strdata,self.server,self.report)
                    raise InfoException(strdata)
            subprocess_call([
                'kexec',
                '--load',
                '--initrd=%s' % (self.safe_load(profile_data,'initrd_local'),),
                '--command-line=%s' % (k_args,),
                self.safe_load(profile_data,'kernel_local')
            ])
            strdata="Kernel loaded; run 'kexec -e' to execute"
            print(strdata)
            self.logger.info(strdata)
            notice_server(strdata,self.server,self.report)
            if self.reboot:
                subprocess_call(['kexec','-e'])
        return self.net_install(after_download)


    #---------------------------------------------------
        
    def get_boot_loader_info(self):
        if ANCIENT_PYTHON:
            # FIXME: implement this to work w/o subprocess
            if os.path.exists("/etc/grub.conf"):
               return (0, "grub")
            else:
               return (0, "lilo") 
        cmd = [ "/sbin/grubby", "--bootloader-probe" ]
        probe_process = sub_process.Popen(cmd, stdout=sub_process.PIPE)
        which_loader = probe_process.communicate()[0]
        return probe_process.returncode, which_loader

    def replace(self):
        """
        Handle morphing an existing system through downloading new
        kernel, new initrd, and installing a kickstart in the initrd,
        then manipulating grub.
        """

        def after_download(self, profile_data):
            use_grubby = False
            use_grub2 = False
            (make, version) = os_release()
            if make in ['ubuntu', 'debian']:
                if not os.path.exists("/usr/sbin/update-grub"):
                    self.logger.error("grub2 is not installed")
                    notice_server("grub2 is not installed",self.server,self.report)
                    raise InfoException("grub2 is not installed")
                use_grub2 = True
            else:
                if not os.path.exists("/sbin/grubby"):
                    self.logger.error("grubby is not installed")
                    self.logger.error("grubby is not installed")
                    raise InfoException("grubby is not installed")
                use_grubby = True

            k_args = self.calc_kernel_args(profile_data,replace_self=1)

            kickstart = self.safe_load(profile_data,'kickstart')
            breed     = self.safe_load(profile_data,'breed')
            if breed =='ubuntu':
                if self.embed_seed:
                    progress = Progress()
                    progress.start()
                    self.build_initrd(
                        self.safe_load(profile_data,'initrd_local'),
                        kickstart,
                        profile_data
                    )
                    progress.stop()
            if not ANCIENT_PYTHON:
                arch_cmd = sub_process.Popen("/bin/uname -m", stdout=sub_process.PIPE, shell=True)
                arch = arch_cmd.communicate()[0]
            else:
                arch = "i386"

            # Validate kernel argument length (limit depends on architecture --
            # see asm-*/setup.h).  For example:
            #   asm-i386/setup.h:#define COMMAND_LINE_SIZE 256
            #   asm-ia64/setup.h:#define COMMAND_LINE_SIZE  512
            #   asm-powerpc/setup.h:#define COMMAND_LINE_SIZE   512
            #   asm-s390/setup.h:#define COMMAND_LINE_SIZE  896
            #   asm-x86_64/setup.h:#define COMMAND_LINE_SIZE    256
            #   arch/x86/include/asm/setup.h:#define COMMAND_LINE_SIZE 2048
            if not ANCIENT_PYTHON:
                if arch.startswith(b"ppc") or arch.startswith(b"ia64"):
                    if len(k_args) > 511:
                        raise InfoException("Kernel options are too long, 512 chars exceeded: %s" % k_args)
                elif arch.startswith(b"s390"):
                    if len(k_args) > 895:
                        raise InfoException("Kernel options are too long, 896 chars exceeded: %s" % k_args)
                elif len(k_args) > 2048:
                    raise InfoException("Kernel options are too long, 2048 chars exceeded: %s" % k_args)
            if self.vncpassword:
                if len(self.vncpassword)>8 or len(self.vncpassword)<6:
                    strdata = "VNC password must be six to eight characters long"
                    self.logger.error(strdata)
                    notice_server(strdata,self.server,self.report)
                    raise InfoException(strdata)
            if use_grubby:
                cmd = [ "/sbin/grubby",
                        "--add-kernel", self.safe_load(profile_data,'kernel_local'),
                        "--initrd", self.safe_load(profile_data,'initrd_local'),
                        "--args", "\"%s\"" % k_args
                ]

                if not self.no_copy_default:
                    cmd.append("--copy-default")

                boot_probe_ret_code, probe_output = self.get_boot_loader_info()
                if boot_probe_ret_code == 0 and string.find(probe_output, "lilo") >= 0:
                    cmd.append("--lilo")

                if self.add_reinstall_entry:
                    cmd.append("--title=Reinstall")
                else:
                    cmd.append("--make-default")
                    cmd.append("--title=kick%s" % int(time.time()))
               
                if self.live_cd:
                    cmd.append("--bad-image-okay")
                    cmd.append("--boot-filesystem=/")
                    cmd.append("--config-file=/tmp/boot/boot/grub/grub.conf")

                # Are we running on ppc?
                if not ANCIENT_PYTHON:
                    if arch.startswith("ppc"):
                        if "grub2" in probe_output:
                            cmd.append("--grub2")
                        else:
                            cmd.append("--yaboot")
                    elif arch.startswith("s390"):
                        cmd.append("--zipl")

                subprocess_call(cmd)

                # Need to remove the root= argument to prevent booting the current OS
                cmd = [
                    "/sbin/grubby",
                    "--update-kernel",
                    self.safe_load(
                        profile_data,
                        'kernel_local'),
                    "--remove-args=root"]

                subprocess_call(cmd)

                # Any post-grubby processing required (e.g. ybin, zipl, lilo)?
                if not ANCIENT_PYTHON and arch.startswith("ppc") and "grub2" not in probe_output:
                    # FIXME - CHRP hardware uses a 'PPC PReP Boot' partition and doesn't require running ybin
                    print("- applying ybin changes")
                    cmd = [ "/sbin/ybin" ]
                    subprocess_call(cmd)
                elif not ANCIENT_PYTHON and arch.startswith("s390"):
                    print("- applying zipl changes")
                    cmd = [ "/sbin/zipl" ]
                    subprocess_call(cmd)
                else:
                    # if grubby --bootloader-probe returns lilo,
                    #    apply lilo changes
                    if boot_probe_ret_code == 0 and string.find(probe_output, "lilo") != -1:
                        print("- applying lilo changes")
                        cmd = [ "/sbin/lilo" ]
                        subprocess_call(cmd)

            elif use_grub2:
                # Use grub2 for --replace-self
                kernel_local = self.safe_load(profile_data,'kernel_local')
                initrd_local = self.safe_load(profile_data,'initrd_local')

                # Set name for grub2 menuentry
                if self.add_reinstall_entry:
                    name = "Reinstall: %s" % profile_data['name']
                else:
                    name = "%s" % profile_data['name']

                # Set paths for Ubuntu/Debian
                # TODO: Add support for other distros when they ship grub2
                if make in ['ubuntu', 'debian']:
                    grub_file = "/etc/grub.d/42_qios"
                    grub_default_file = "/etc/default/grub"
                    cmd = ["update-grub"]
                    default_cmd = ['sed', '-i', 's/^GRUB_DEFAULT\=.*$/GRUB_DEFAULT="%s"/g' % name, grub_default_file]
                kernel_boot = kernel_local[5:]
                initrd_boot = initrd_local[5:]
                # Create grub2 menuentry
                grub_entry = """
cat <<EOF
menuentry "%s" {
    linux %s %s
    initrd %s
}
EOF
                """ % (name,kernel_boot, k_args, initrd_boot)
                # Save grub2 menuentry
                fd = open(grub_file,"w")
                fd.write(grub_entry)
                fd.close()
                os.chmod(grub_file, 0o755)

                # Set default grub entry for reboot
                if not self.add_reinstall_entry:
                    print("- setting grub2 default entry")
                    subprocess_call(default_cmd)

                # Run update-grub
                subprocess_call(cmd)

            if not self.add_reinstall_entry:
                print("- reboot to apply changes")
                self.logger.info("- reboot to apply changes")
                notice_server("- reboot to apply changes",self.server,self.report)
            else:
                print("- reinstallation entry added")
                self.logger.info("- reinstallation entry added")
                notice_server("- reinstallation entry added",self.server,self.report)
            if self.reboot:
                notice_server("- booting new kernel",self.server,self.report)
                subprocess_call(['reboot'])

        return self.net_install(after_download)

    #---------------------------------------------------

    def get_insert_script(self,initrd):
        """
        Create bash script for inserting kickstart into initrd.
        Code heavily borrowed from internal auto-ks scripts.
        """
        return r"""
        cd /var/spool/qios
        mkdir initrd
        gzip -dc %s > initrd.tmp || xz -dc %s > initrd.tmp
        if mount -o loop -t ext2 initrd.tmp initrd >&/dev/null ; then
            cp preseed.cfg initrd/
            ln initrd/preseed.cfg initrd/tmp/preseed.cfg
            umount initrd
            gzip -c initrd.tmp > initrd_final
        else
            echo "mount failed; treating initrd as a cpio archive..."
            cd initrd
            cpio -id <../initrd.tmp
            cp /var/spool/qios/preseed.cfg .
            ln preseed.cfg tmp/preseed.cfg
            find . | cpio -o -H newc | gzip -9 > ../initrd_final
            echo "...done"
        fi
        """ % (initrd, initrd)

    #---------------------------------------------------

    def build_initrd(self,initrd,kickstart,data):
        """
        Crack open an initrd and install the kickstart file.
        """
        self.logger.info("Building initrd")
        # save kickstart to file
        ksdata = urlread(kickstart)
        fd = open("/var/spool/qios/preseed.cfg","wb+")
        if ksdata is not None:
            fd.write(ksdata)
        fd.close()

        # handle insertion of kickstart based on type of initrd
        fd = open("/var/spool/qios/insert.sh","w+")
        fd.write(self.get_insert_script(initrd))
        fd.close()
        subprocess_call([ "/bin/bash", "/var/spool/qios/insert.sh" ])
        shutil.copyfile("/var/spool/qios/initrd_final", initrd)
        self.logger.info("New initrd consists of preseed.cfg has been bulided")
    #---------------------------------------------------

    def connect_fail(self):
        raise InfoException("Could not communicate with %s:%s" % (self.server, self.port))

    #---------------------------------------------------

    def get_data(self,what,name=None):
        try:
            if what[-1] == "s":
                data = getattr(self.xmlrpc_server, "get_%s" % what)()
            else:
                data = getattr(self.xmlrpc_server, "get_%s_for_koan" % what)(name)
        except:
            traceback.print_exc()
            self.connect_fail()
        if data == {}:
            raise InfoException("No entry/entries found")
        return data
    
    #---------------------------------------------------

    def get_ips(self,strdata):
        """
        Return a list of IP address strings found in argument.
        warning: not IPv6 friendly
        """
        return re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',strdata)

    #---------------------------------------------------

    def get_macs(self,strdata):
        """
        Return a list of MAC address strings found in argument.
        """
        return re.findall(r'[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F:0-9]{2}:[A-F:0-9]{2}', strdata.upper())

    #---------------------------------------------------

    def is_ip(self,strdata):
        """
        Is strdata an IP?
        warning: not IPv6 friendly
        """
        return self.get_ips(strdata) and True or False

    #---------------------------------------------------

    def is_mac(self,strdata):
        """
        Return whether the argument is a mac address.
        """
        return self.get_macs(strdata) and True or False

    #---------------------------------------------------

    def get_distro_files(self,profile_data, download_root):
        """
        Using distro data (fetched from bootconf tree), determine
        what kernel and initrd to download, and save them locally.
        """
        os.chdir(download_root)
        distro = self.safe_load(profile_data,'distro')
        kernel = self.safe_load(profile_data,'kernel')
        initrd = self.safe_load(profile_data,'initrd')
        kernel_short = os.path.basename(kernel)
        initrd_short = os.path.basename(initrd)
        kernel_save = "%s/%s_qios" % (download_root, kernel_short)
        initrd_save = "%s/%s_qios" % (download_root, initrd_short)

        if self.server:
            if kernel[0] == "/":
                kernel = "http://%s/cobbler/images/%s/%s" % (profile_data["http_server"], distro, kernel_short)
            if initrd[0] == "/":
                initrd = "http://%s/cobbler/images/%s/%s" % (profile_data["http_server"], distro, initrd_short)

        try:
            print("downloading initrd %s to %s" % (initrd_short, initrd_save))
            print("url=%s" % initrd)
            urlgrab(initrd,initrd_save)

            print("downloading kernel %s to %s" % (kernel_short, kernel_save))
            print("url=%s" % kernel)
            urlgrab(kernel,kernel_save)
        except:
            traceback.print_exc()
            raise InfoException("error downloading files")
        profile_data['kernel_local'] = kernel_save
        profile_data['initrd_local'] = initrd_save

    #---------------------------------------------------

    def calc_kernel_args(self, pd, replace_self=0):
        kickstart = self.safe_load(pd,'kickstart')
        options   = self.safe_load(pd,'kernel_options',default='')
        breed     = self.safe_load(pd,'breed')
        os_version= self.safe_load(pd,'os_version')

        kextra    = ""
        if kickstart is not None and kickstart != "":
            if breed is not None and breed == "suse":
                kextra = "autoyast=" + kickstart
                if self.drive:
                    kextra += " insecure=1 dud=%s" %self.drive
                if self.vncpassword:
                    kextra += " vncpassword=%s vnc=1 "%self.vncpassword
                if self.sshpassword:
                    kextra += " sshpassword=%s ssh=1 "%self.sshpassword
            elif breed is not None and breed == "debian" or breed =="ubuntu":
                kextra = "netcfg/disable_autoconfig=true auto-install/enable=true priority=critical url=" + kickstart
            else:
                kextra = "ks=" + kickstart
                if os_version[-1] == '6':
                    if self.drive:
                        kextra += " dd=%s" %self.drive
                    if self.vncpassword:
                        kextra += " vnc vncpassword=%s"%self.vncpassword
                    if self.sshpassword:
                        kextra += " sshd=1"
                elif os_version[-1] == '7':
                    if self.drive:
                        kextra += " inst.dd=%s" %self.drive
                    if self.vncpassword:
                        kextra += " inst.vnc inst.vncpassword=%s"%self.vncpassword
                    if self.sshpassword:
                        kextra += " inst.sshd"

        if options !="":
            kextra = kextra + " " + options
        # parser issues?  lang needs a trailing = and somehow doesn't have it.

        # convert the from-cobbler options back to a hash
        # so that we can override it in a way that works as intended

        hashv = input_string_or_hash(kextra)

        if breed == "redhat" or breed == "suse" or breed == "debian" or breed == "ubuntu":
            if os.path.exists("/proc/net/bonding/bond0"):
                interface_name = 'bond0'
            else:
                interface_name = 'eth0'
            interfaces = self.safe_load(pd, "interfaces")
            if interface_name.startswith("eth"):
                alt_interface_name = interface_name.replace("eth", "intf")
                interface_data = self.safe_load(interfaces, interface_name, alt_interface_name)
            else:
                interface_data = self.safe_load(interfaces, interface_name)

            ip = self.safe_load(interface_data, "ip_address")
            netmask = self.safe_load(interface_data, "netmask")
            gateway = self.safe_load(pd, "gateway")
            dns = self.safe_load(pd, "name_servers")
            hostname = self.safe_load(interface_data, "dns_name")

            if breed == "debian" or breed == "ubuntu":
                hostname = self.safe_load(pd, "hostname")
                name = self.safe_load(pd, "name")

                if hostname != "" or name != "":
                    if hostname != "":
                        # if this is a FQDN, grab the first bit
                        my_hostname = hostname.split(".")[0]
                        _domain = hostname.split(".")[1:]
                        if _domain:
                           my_domain = ".".join(_domain)
                    else:
                        my_hostname = name.split(".")[0]
                        _domain = name.split(".")[1:]
                        if _domain:
                           my_domain = ".".join(_domain)
                    hashv["hostname"] = my_hostname
                    hashv["domain"] = my_domain

            if breed == "suse":
                hashv["netdevice"] = self.safe_load(pd, "mac_address_eth0")
                hashv["install"] = self.safe_load(pd, "install_tree")
            else:
                hashv["ksdevice"] = self.safe_load(pd, "mac_address_eth0")
            if ip is not None:
                if breed == "suse":
                    hashv["hostip"] = ip
                elif breed == "debian" or breed == "ubuntu":
                    hashv["netcfg/get_ipaddress"] = ip
                else:
                    hashv["ip"] = ip
            if netmask is not None:
                if breed == "debian" or breed == "ubuntu":
                    hashv["netcfg/get_netmask"] = netmask
                else:
                    hashv["netmask"] = netmask
            if gateway is not None:
                if breed == "debian" or breed == "ubuntu":
                    hashv["netcfg/get_gateway"] = gateway
                else:
                    hashv["gateway"] = gateway
            if dns is not None:
                if breed == "suse":
                    hashv["nameserver"] =  " ".join(dns)
                elif breed == "debian" or breed == "ubuntu":
                    hashv["netcfg/get_nameservers"] = " ".join(dns)
                else:
                    hashv["nameserver"] =  " ".join(dns)
        """
        if replace_self and self.embed_kickstart:
           hashv["ks"] = "file:ks.cfg"
        """
        if self.kopts_override is not None:
           hash2 = input_string_or_hash(self.kopts_override)
           hashv.update(hash2)
        options = hash_to_string(hashv)
        options = options.replace("lang ","lang= ")
        # if using ksdevice=bootif that only works for PXE so replace
        # it with something that will work
        options = options.replace("ksdevice=bootif","ksdevice=link")
        return options

    #---------------------------------------------------

if __name__ == "__main__":
    main()
