# -*- coding: utf-8 -*-
# support VMware ESXi 6.5.0 build-4887370
from pyVim import connect
from pyVmomi import vim
import json
class VcenterApi(object):
    """
    收集Vcenter中数据中心，主机集群，主机，网络，虚拟机，的信息
    """
    def __init__(self, host, user, pwd):
        self.si = connect.ConnectNoSSL(host=host, user=user, pwd=pwd)
        self.content = self.si.RetrieveContent()
        datacenter = self.content.rootFolder.childEntity[0]
        self.datacentername = datacenter.name
        #print(self.datacentername)
    def get_cluster_list(self):
        """
        获取所有机器资源使用情况
        1.CPU
        2.内存
        3.磁盘
        :return:
        """
        # 获取集群视图
        objview = self.content.viewManager.CreateContainerView(self.content.rootFolder,[vim.ComputeResource],True)
        # 获取集群对象
        clusters = objview.view
        # 销毁视图
        objview.Destroy()
        redata = []
        for cluster in clusters:
            summary = cluster.summary
            cpuusage = 0
            memusage = 0
            vmcount = 0
            for host in cluster.host:
                cpuusage += host.summary.quickStats.overallCpuUsage
                memusage += host.summary.quickStats.overallMemoryUsage
                vmcount += len(host.vm)
            totaldatastore = 0
            datastorefree = 0
            for datastore in cluster.datastore:
                totaldatastore += datastore.summary.capacity
                datastorefree += datastore.summary.freeSpace
            clusterdata = {
                #集群名称
                "cluster_name": cluster.name,
                #集群状态
                "overall_status": summary.overallStatus,
                #总主机数
                "num_hosts": summary.numHosts,
                #cpu颗数
                "num_cpu_cores": summary.numCpuCores,
                #总cpu
                "cpu_total": "%.2f GHz" % (summary.totalCpu / 1000.0),
                #已使用cpu
                "cpu_usage": "%.2f GHz" % (cpuusage / 1000.0),
                #总内存
                "mem_total": "%.2f GB" % (summary.totalMemory / 1024 / 1024 / 1024.0),
                #已使用mem
                "mem_usage": "%.2f GB" % (memusage / 1024.0),
                #总存储
                "total_data_store": "%.2f T" % (totaldatastore / 1024 / 1024 / 1024 / 1024.0),
                #可用存储
                "datastore_free": "%.2f T" % (datastorefree / 1024 / 1024 / 1024 / 1024.0),
                #vm数量
                "vm_count": vmcount,
                "datacenter_name": self.datacentername,
                }
            redata.append(clusterdata)
        return redata

    def print_vm_info(self, virtual_machine):
        summary = virtual_machine.summary
        if summary.guest.ipAddress:
            return
        self.count+=1
        print("Name          :  %s"%summary.config.name)
        print("Template      :  %s"%summary.config.template)
        print("Path          :  %s"%summary.config.vmPathName)
        print("Guest         :  %s"%summary.config.guestFullName)
        print("Instance UUID :  %s"%summary.config.instanceUuid)
        print("Bios UUID     :  %s"%summary.config.uuid)
        annotation = summary.config.annotation
        if annotation:
            print ("Annotation : %s"%annotation)
        print("State      : %s"%summary.runtime.powerState)
        if summary.guest is not None:
            ip_address = summary.guest.ipAddress
            tools_version = summary.guest.toolsStatus
            if tools_version is not None:
                print("VMware-tools: %s"%tools_version)
            else:
                print("Vmware-tools: None")
            if ip_address:
                print("IP         : %s"%ip_address)
            else:
                print("IP         : None")
        if summary.runtime.question is not None:
            print("Question  : %s"%summary.runtime.question.text)

    def get_all_vm(self):
        self.count = 0
        container = self.content.rootFolder
        viewType = [vim.VirtualMachine]
        recursive = True
        containerView = self.content.viewManager.CreateContainerView(
            container, viewType, recursive)
        children = containerView.view
        for child in children:
            self.print_vm_info(child)
    def get_vm_count(self):
        container = self.content.rootFolder
        viewType = [vim.VirtualMachine]
        recursive = True
        containerView = self.content.viewManager.CreateContainerView(
            container, viewType, recursive)
        children = containerView.view
        return len(children)

    def get_datacenter_list(self):
        """
        数据中心信息
        :return:
        """
        objview = self.content.viewManager.CreateContainerView(self.content.rootFolder,[vim.ComputeResource],True)
        # 获取集群对象
        clusters = objview.view
        # 销毁视图
        objview.Destroy()
        # cpu总大小
        cputotal = 0
        # 使用cpu
        cpuusage = 0
        memtotal = 0
        memusage = 0
        totaldatastore = 0
        datastorefree = 0
        numHosts = 0
        numCpuCores = 0
        datastore_list = []
        for cluster in clusters:
            summary = cluster.summary
            for host in cluster.host:
                cpuusage += host.summary.quickStats.overallCpuUsage
                memusage += host.summary.quickStats.overallMemoryUsage

            for datastore in cluster.datastore:
                datastore_list.append(datastore)
            cputotal += summary.totalCpu
            memtotal += summary.totalMemory
            numHosts += summary.numHosts
            numCpuCores += summary.numCpuCores
        for datastore in set(datastore_list):
            totaldatastore += datastore.summary.capacity
            datastorefree += datastore.summary.freeSpace
        return {
            "cpu_total": "%.2f GHz" % (cputotal / 1000.0),
            "cpu_usage": "%.2f GHz" % (cpuusage / 1000.0),
            "mem_total": "%.2f GB" % (memtotal / 1024 / 1024 / 1024.0),
            "mem_usage": "%.2f GB" % (memusage / 1024.0),
            "total_datastore": "%.2f T" % (totaldatastore/1024/1024/1024/1024.0),
            "datastore_free": "%.2f T" % (datastorefree/1024/1024/1024/1024.0),
            "num_hosts": numHosts,
            "num_cpu_cores": numCpuCores,
            "vm_count": self.get_vm_count(),
            "datacenter_name": self.datacentername,
        }

    def get_datastore_list(self):
        objview = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.Datastore], True)
        objs = objview.view
        objview.Destroy()
        # 存储部分
        # 存储集群环境-通过单个存储汇总得到存储集群得容量情况
        cluster_store_dict = {}
        datastore_list = []
        for i in objs:
            capacity = "%.2f G" % (i.summary.capacity/1024/1024/1024.0)
            freespace = "%.2f G" % (i.summary.freeSpace/1024/1024/1024.0)
            datastore_summary = {
                "cluster_store_name": "默认集群目录" if i.parent.name=="datastore" else i.parent.name,
                "datacentername": self.datacentername,
                "datastore": str(i.summary.datastore),
                "name": i.summary.name,
                #唯一定位器
                "url": i.summary.url,
                "capacity": capacity,
                "freespace": freespace,
                "type": i.summary.type,
                # 连接状态
                "accessible": i.summary.accessible,
                #多台主机连接
                "multiplehostaccess": i.summary.multipleHostAccess,
                #当前维护模式状态
                "maintenancemode": i.summary.maintenanceMode
            }
            datastore_list.append(datastore_summary)
        return datastore_list

    def get_host_list(self):
        """
        vcenter下物理主机信息
        :return:
        """
        objview = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.HostSystem], True)
        objs = objview.view
        objview.Destroy()
        host_list = []
        for host in objs:
            sn = []
            for i in host.summary.hardware.otherIdentifyingInfo:
                if isinstance(i, vim.host.SystemIdentificationInfo):
                    sn.append(i.identifierValue)
            data = {
                "name": host.name,
                # EXSI版本
                "fullname":host.summary.config.product.fullName,
                "cluster_name": host.parent.name,
                "datacenter_name": self.datacentername,
                "network": [network.name for network in host.network],
                "datastore": [datastore.name for datastore in host.datastore],
                # 主机连接状态
                "connection_state": host.runtime.connectionState,
                # 主机电源状态
                "power_state": host.runtime.powerState,
                # 主机是否处于维护模式
                "maintenance_mode": host.runtime.inMaintenanceMode,
                # 厂商
                "vendor": host.summary.hardware.vendor,
                # 硬件型号
                "model": host.summary.hardware.model,
                "SN": sn,
                "uuid": host.summary.hardware.uuid,
                # cpu型号
                "cpu_model": host.summary.hardware.cpuModel,
                # cpu插槽数
                "cpu_pkgs": host.summary.hardware.numCpuPkgs,
                # cpu核心数
                "cpu_cores": host.summary.hardware.numCpuCores,
                # 逻辑处理器数
                "cpu_threads": host.summary.hardware.numCpuThreads,
                # cpu频率Mhz
                "cpu_Ghz": "%.2f" % (host.summary.hardware.cpuMhz/1000.0),
                # 已使用cpuGhz
                "cpu_usage": "%.2f" % (host.summary.quickStats.overallCpuUsage/1000.0),
                # 内存大小 G
                "mem_size": "%.2f" % (host.summary.hardware.memorySize / 1024 / 1024 / 1024.0),
                "mem_usage": "%.2f" % (host.summary.quickStats.overallMemoryUsage/ 1024.0),
                # 运行时间
                "uptime": host.summary.quickStats.uptime,
            }
            print("规格:%sC%s核 %sG"%(data.get('cpu_pkgs'),data.get('cpu_cores'),data.get('mem_size')))
            print("CPU利用率:%.2f"%(float(data.get('cpu_usage'))/((float(data.get('cpu_Ghz'))*float(data.get('cpu_cores'))))))
            print("CPU线程数:%s"%data.get('cpu_cores'))
            print("CPU频率:%s"%data.get('cpu_Ghz'))
            print("CPU型号:%s"%data.get('cpu_model'))
            print("MEM利用率:%.2f"%(float(data.get('mem_usage'))/float(data.get('mem_size'))))
            print("ESXI_OS:%s"%data.get('fullname'))
            print("厂商:%s"%data.get('vendor'))
            print("硬件型号:%s"%data.get('model'))
            print("硬件SN:%s"%data.get('sn'))
            host_list.append(data)
        return host_list

    def get_networkport_group_list(self):
        objview = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.Network], True)
        objs = objview.view
        objview.Destroy()
        network_list =[]
        for networkobj in objs:
            # network = networkobj.summary.network
            # 分布式交换机名称
            try:
                distributedvirtualswitchname = networkobj.config.distributedVirtualSwitch.name
                key = networkobj.config.key
                vlanid = networkobj.config.defaultPortConfig.vlan.vlanId
                link_type = "上行链路端口组"
                if not isinstance(vlanid, int):
                    vlanid = "0-4094"
                    link_type = "分布式端口组"
            except AttributeError:
                continue
            data = {
                "name": networkobj.name,
                "datacenter_name": self.datacentername,
                "key": key,
                "accessible": networkobj.summary.accessible,
                "distributed_virtual_switch_name": distributedvirtualswitchname,
                "vlan_id": vlanid,
                "link_type": link_type,
            }
            network_list.append(data)
        return network_list

    def get_vm_list(self):
        objview = self.content.viewManager.CreateContainerView(self.content.rootFolder, [vim.VirtualMachine], True)
        objs = objview.view
        objview.Destroy()
        vm_list = []
        for vm_machine in objs:
            # 虚拟磁盘信息
            virtualdisk = []
            try:
                for disk in vm_machine.config.hardware.device:
                    try:
                        if hasattr(disk, "diskObjectId"):
                            label = disk.deviceInfo.label
                            capacityinkb = disk.capacityInKB
                            virtualdisk.append({"label": label, "capacityinkb": capacityinkb})
                    except AttributeError:
                        pass
            except AttributeError:
                continue
            ipaddress = vm_machine.guest.ipAddress
            other_ip = set()
            for vmnet in vm_machine.guest.net:
                for ip in vmnet.ipAddress:
                    other_ip.add(ip)
            data = {
                # 虚拟机名称
                "name": vm_machine.name,
                # EXSI主机
                "host": vm_machine.summary.runtime.host.name,
                "datacenter_name": self.datacentername,
                "ip_address": ipaddress,
                "other_ip": json.dumps(list(other_ip)),
                "connection_state": vm_machine.summary.runtime.connectionState,
                "power_state": vm_machine.summary.runtime.powerState,
                # vmwareTools 安装情况
                "tools_status": vm_machine.summary.guest.toolsStatus,
                # 系统内hostname
                "hostname": vm_machine.summary.guest.hostName,
                "uuid": vm_machine.summary.config.uuid,
                # 是否模版
                "template": vm_machine.summary.config.template,
                # vm文件路径
                "vm_path_name": vm_machine.summary.config.vmPathName,
                # 虚拟cpu 颗数
                "cpu_cores": vm_machine.summary.config.numCpu,
                "mem_size": "%.2f" %(vm_machine.summary.config.memorySizeMB/1024.0),
                "num_ethernet_cards": vm_machine.summary.config.numEthernetCards,
                "num_virtual_disks": vm_machine.summary.config.numVirtualDisks,
                "storage_usage": "%.2fG" % (vm_machine.summary.storage.committed/1024/1024/1024.0),
                "cpu_usage": vm_machine.summary.quickStats.overallCpuUsage,
                "mem_usage": vm_machine.summary.quickStats.guestMemoryUsage,
                "uptime": vm_machine.summary.quickStats.uptimeSeconds,
                # 运行状态
                "over_all_status": vm_machine.summary.overallStatus,
                "network": [i.name for i in vm_machine.network],
                "virtual_disk_info": json.dumps(virtualdisk),
                "os": vm_machine.summary.config.guestFullName,
            }
            print("HOST:%s"%data.get('host'))
            print("IP:%s"%data.get('ip_address'))
            print("规格:%sC %sG"%(data.get('cpu_cores'),
                data.get('mem_size')))
            print("OS:%s"%data.get('os'))
            print("电源状态:%s"%data.get('power_state'))
            print("硬盘:%s"%data.get('virtual_disk_info'))
            vm_list.append(data)
        return vm_list
