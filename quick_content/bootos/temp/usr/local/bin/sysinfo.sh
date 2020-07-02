#!/usr/bin/env bash
# version 0.1
export PATH=/bin:/sbin:/usr/bin:/usr/sbin
export LC_ALL=C

exec 3>&1
exec &>/dev/null

# serial & manufacturer
if dmidecode | grep -qEi 'VMware|VirtualBox|KVM|Xen|Parallels'; then
    SN=$(sed q /sys/class/net/*/address)
else
    SN=$(dmidecode -s system-serial-number 2>/dev/null | awk '/^[^#]/ { print $1 }')
fi
MANUFACTURER=$(dmidecode -s system-manufacturer | awk '/^[^#]/ { print $1 }')
PRODUCT_NAME=$(dmidecode -s system-product-name | awk '/^[^#]/')

# raid
RAID_DEVICE=$(lspci | grep RAID | sed ':a;N;$!ba;s/\n/\\n/g')

# nic
NIC_DEVICE=$(lspci | grep Ethernet | sed ':a;N;$!ba;s/\n/\\n/g')

# oob
OOB_IP=$(ipmitool lan print | awk '/IP Address[[:blank:]]+:/ { print $NF }')

# cpu info
CPU_MODEL=$(awk -F':' '/model name/ { print $NF; exit }' /proc/cpuinfo)
CPU_CORE=$(grep -c 'processor' /proc/cpuinfo)

# memory info
MEMORY_SUM=$(dmidecode -t memory | awk '/^[[:blank:]]+Size.*MB/ { sum += $(NF-1) } END { printf("%d", sum) }')
MEMORY=$(dmidecode -t memory | awk -F'[: ]' '/^[[:blank:]]+Size.*MB/ { printf("{\"Name\":\"\",\"size\":\"%s MB\"},", $(NF-1)) }' | sed 's/,$//')
[[ "$MEMORY_SUM" -eq 0 ]] && MEMORY_SUM=$(awk '/MemTotal/ { printf("%d"), $2/1024 }' /proc/meminfo)

# disk info
if lspci | grep -q 'RAID bus controller.*MegaRAID'; then
    rpm -q MegaCli || yum -y install MegaCli
    DISK=$(/opt/MegaRAID/MegaCli/MegaCli64 -PDList -aALL | awk '/Raw Size/ { printf("{\"Name\":\"\",\"size\":\"%s %s\"},", $3, $4) }' | sed 's/,$//')
    DISK_SUM=$(/opt/MegaRAID/MegaCli/MegaCli64 -PDList -aALL | awk '/Raw Size/ { if ($4 == "TB") { sum0 += $3 * 1000 } else { sum1 += $3 } } END { printf("%d", sum0 + sum1) }')
elif lspci | grep -q 'RAID bus controller.*Hewlett-Packard'; then
    rpm -q hpssacli || yum -y install hpssacli
    _slot=$(/usr/sbin/hpssacli ctrl all show status | awk '/Slot/ { print $6 }' | sed q)
    DISK=$(/usr/sbin/hpssacli ctrl slot=$_slot pd all show status | awk '{ sub(/\):/, "", $8); printf("{\"Name\":\"\",\"size\":\"%s %s\"},", $7, $8) }' | sed 's/,$//')
    DISK_SUM=$(/usr/sbin/hpssacli ctrl slot=$_slot pd all show status | awk '{ if ($8 ~ /TB/) { sum0 += $7 * 1000 } else { sum1 += $7 } } END { printf("%d", sum0 + sum1) }')
else
    DISK=$(fdisk -lu | awk '/^Disk.*bytes/ { gsub(/,/, ""); printf("{\"Name\":\"\",\"size\":\"%s %s\"},", $3, $4) }' | sed 's/,$//')
    DISK_SUM=$(fdisk -lu | awk '/^Disk.*bytes/ { sum += $3 } END { printf("%d", sum) }')
fi

# network info
NIC=$(
    for _dev in /sys/class/net/*/device
    do
        _nic=$(cut -d'/' -f5 <<< $_dev)
        _mac=$(cat /sys/class/net/$_nic/address)
        _ip=$(ip a s $_nic | awk '/inet/ { gsub(/\/.*/, ""); print $2 }')
        echo -n "{\"Name\":\"$_nic\",\"Mac\":\"$_mac\",\"Ip\":\"$_ip\"},"
    done | sed 's/,$//'
)

# is vm
dmidecode | grep -qEi 'VMware|VirtualBox|KVM|Xen|Parallels' && IS_VM=Yes || IS_VM=No

# return json
cat >&3 <<EOF
{"Sn":"$SN","Company":"$MANUFACTURER","ModelName":"$PRODUCT_NAME","Motherboard":{"Name":"","Model":""},"Raid":"$RAID_DEVICE","NicDevice":"$NIC_DEVICE","Oob":"$OOB_IP","Cpu":{"Model":"$CPU_MODEL","Core":"$CPU_CORE"},"Memory":[$MEMORY],"MemorySum":$MEMORY_SUM,"DiskSum":$DISK_SUM,"Nic":[$NIC],"Disk":[$DISK],"IsVm":"$IS_VM"}
EOF
