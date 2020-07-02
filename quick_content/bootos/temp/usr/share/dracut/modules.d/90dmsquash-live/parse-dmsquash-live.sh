#!/bin/sh
# live images are specified with
# root=live:backingdev

[ -z "$root" ] && root=$(getarg root=)

# support legacy syntax of passing liveimg and then just the base root
if getarg liveimg; then
    liveroot="live:$root"
fi

if [ "${root%%:*}" = "live" ] ; then
    liveroot=$root
fi

[ "${liveroot%%:*}" = "live" ] || return

case "$liveroot" in
    live:LABEL=*|LABEL=*)
	root="${root#live:}"
	root="$(echo $root | sed 's,/,\\x2f,g')"
	root="live:/dev/disk/by-label/${root#LABEL=}"
        rootok=1 ;;
    live:CDLABEL=*|CDLABEL=*)
	root="${root#live:}"
	root="$(echo $root | sed 's,/,\\x2f,g')"
	root="live:/dev/disk/by-label/${root#CDLABEL=}"
        rootok=1 ;;
    live:UUID=*|UUID=*)
	root="${root#live:}"
	root="live:/dev/disk/by-uuid/${root#UUID=}"
        rootok=1 ;;
    live:/*.[Ii][Ss][Oo]|/*.[Ii][Ss][Oo])
	root="${root#live:}"
	root="liveiso:${root}"
	rootok=1 ;;
    live:/dev/*)
        rootok=1 ;;
esac
info "root was $root, liveroot is now $liveroot"

if [ "${root##live:/dev/}" != "$root" ]; then
    [ -d /dev/.udev/rules.d ] || mkdir -p /dev/.udev/rules.d
    {
        printf 'KERNEL=="%s", SYMLINK+="live"\n' \
            ${root#live:/dev/}
        printf 'SYMLINK=="%s", SYMLINK+="live"\n' \
            ${root#live:/dev/}
    } >> /dev/.udev/rules.d/99-live-mount.rules
    {
        printf 'KERNEL=="%s", RUN+="/sbin/initqueue --settled --onetime --unique /sbin/dmsquash-live-root $env{DEVNAME}"\n' \
            ${root#live:/dev/}
        printf 'SYMLINK=="%s", RUN+="/sbin/initqueue --settled --onetime --unique /sbin/dmsquash-live-root $env{DEVNAME}"\n' \
            ${root#live:/dev/}
    } >> /etc/udev/rules.d/98-dracut-20-live-squash.rules
    echo '[ -e /dev/live ]' > /initqueue-finished/dmsquash.sh
    root=/dev/mapper/live-rw
    unset rootok
fi
