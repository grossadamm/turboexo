#!/bin/bash
set -euo pipefail

readonly SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
readonly TSDASH_DIR="/home/dietpi/TSDash"
restart_dashboard=false

if [[ ${1:-} == "--restart-dashboard" ]]; then
    restart_dashboard=true
elif [[ $# -ne 0 ]]; then
    echo "usage: sudo $0 [--restart-dashboard]" >&2
    exit 2
fi
if [[ $(id -u) -ne 0 ]]; then
    echo "Run as root." >&2
    exit 2
fi
for command in grep install modprobe mountpoint systemctl systemd-analyze; do
    command -v "$command" >/dev/null || {
        echo "Missing required command: $command" >&2
        exit 2
    }
done

kernel_config="/boot/config-$(uname -r)"
grep -q '^CONFIG_GPIO_MOCKUP=m$' "$kernel_config" || {
    echo "The running kernel does not provide gpio-mockup as a module." >&2
    exit 2
}
grep -q '^CONFIG_GPIO_SYSFS=y$' "$kernel_config" || {
    echo "The running kernel does not provide legacy GPIO sysfs." >&2
    exit 2
}
[[ -d "$TSDASH_DIR" ]] || {
    echo "TSDash directory not found: $TSDASH_DIR" >&2
    exit 2
}

"$SCRIPT_DIR/pi4j-bridge/install.sh"

install -m 0755 "$SCRIPT_DIR/turboexo-key-input-setup.sh" \
    /usr/local/libexec/turboexo-key-input-setup.sh
install -m 0755 "$SCRIPT_DIR/pi-ups-monitor.py" \
    /usr/local/libexec/pi-ups-monitor.py
install -m 0755 "$SCRIPT_DIR/configure-tsdash-key-input.sh" \
    /usr/local/libexec/configure-tsdash-key-input.sh
install -m 0644 "$SCRIPT_DIR/turboexo-key-input.service" \
    /etc/systemd/system/turboexo-key-input.service
install -m 0644 "$SCRIPT_DIR/pi-ups-monitor.service" \
    /etc/systemd/system/pi-ups-monitor.service
install -d -m 0755 /etc/systemd/system/getty@tty1.service.d
install -m 0644 "$SCRIPT_DIR/getty-tty1-key-input.conf" \
    /etc/systemd/system/getty@tty1.service.d/turboexo-key-input.conf
install -o dietpi -g dietpi -m 0755 "$SCRIPT_DIR/start-turboexo-dash.sh" \
    "$TSDASH_DIR/start-turboexo-dash.sh"

systemd-analyze verify \
    /etc/systemd/system/turboexo-key-input.service \
    /etc/systemd/system/pi-ups-monitor.service
systemctl daemon-reload
systemctl enable turboexo-key-input.service pi-ups-monitor.service
systemctl restart turboexo-key-input.service
systemctl restart pi-ups-monitor.service

if [[ $restart_dashboard == true ]]; then
    /usr/local/libexec/configure-tsdash-key-input.sh
    systemctl restart getty@tty1
else
    echo "Configure and restart TSDash when ready:"
    echo "  /usr/local/libexec/configure-tsdash-key-input.sh"
    echo "  sudo systemctl restart getty@tty1"
fi
