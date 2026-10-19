#!/bin/bash
set -u

TIMELINE_FILE=/run/turboexo-boot-timeline.log
DEADLINE_SECONDS=90

: > "$TIMELINE_FILE"

mark() {
    local event=$1
    local uptime
    uptime=$(cut -d' ' -f1 /proc/uptime)
    printf '%s uptime=%s\n' "$event" "$uptime" >> "$TIMELINE_FILE"
    logger -t turboexo-boot-timeline "$event uptime=$uptime"
}

mark observer-start

xorg_seen=0
x_root_seen=0
mpv_seen=0
ready_seen=0
painted_seen=0
revealed_seen=0
start_seconds=${SECONDS}

while (( SECONDS - start_seconds < DEADLINE_SECONDS )); do
    if (( xorg_seen == 0 )) && pgrep -x Xorg >/dev/null 2>&1; then
        mark xorg-started
        xorg_seen=1
    fi
    # xinitrc creates this log only after feh has returned, so it is the closest
    # external marker for the static X root having been painted.
    if (( x_root_seen == 0 )) && [[ -e /tmp/turboexo-picom.log ]]; then
        mark x-root-painted
        x_root_seen=1
    fi
    if (( mpv_seen == 0 )) && [[ -e /tmp/turboexo-overlay-visible ]]; then
        mark mpv-visible
        mpv_seen=1
    fi
    if (( ready_seen == 0 )) && [[ -e /tmp/turboexo-dash-ready ]]; then
        mark tsdash-ready
        ready_seen=1
    fi
    if (( painted_seen == 0 )) && [[ -e /tmp/turboexo-dash-painted ]]; then
        mark tsdash-painted
        painted_seen=1
    fi
    if (( revealed_seen == 0 )) && [[ -e /tmp/turboexo-overlay-revealed ]]; then
        mark tsdash-revealed
        revealed_seen=1
    fi

    if (( x_root_seen && mpv_seen && ready_seen && painted_seen && revealed_seen )); then
        break
    fi
    sleep 0.05
done

mark observer-finished
