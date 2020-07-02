#!/bin/sh

if ! getarg rd_NO_MULTIPATH && [ -e /etc/multipath.conf ]; then
    modprobe dm-multipath
    multipathd -B || multipathd
else
    rm /etc/udev/rules.d/??-multipath.rules 2>/dev/null    
fi

