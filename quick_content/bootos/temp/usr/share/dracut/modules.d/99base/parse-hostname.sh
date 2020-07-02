type hostname >/dev/null 2>&1 || \
    hostname() {
        if [ -n "$1" ]; then
            printf -- "%s" "$1" > /proc/sys/kernel/hostname
        else
            cat /proc/sys/kernel/hostname
        fi
}

if hname=$(getarg hostname=); then
    hostname "$hname"
fi
