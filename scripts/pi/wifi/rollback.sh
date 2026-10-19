#!/usr/bin/env bash
# Installed beside the protected pre-install wpa_supplicant.conf snapshot.
set -euo pipefail
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
snapshot=$(cd -- "$(dirname -- "$0")" && pwd)
[[ $EUID -eq 0 && -f "$snapshot/wpa_supplicant.conf" ]] || exit 1
logger -t turboexo-wifi 'Rolling back hotspot trial'
systemctl disable --now turboexo-dhcp.service turboexo-hostapd.service turboexo-ap0.service || true
for unit in turboexo-dhcp.service turboexo-hostapd.service turboexo-ap0.service; do
    state=$(systemctl show "$unit" -p ActiveState --value 2>/dev/null || true)
    case "$state" in
        inactive|failed|"") ;;
        *) echo "$unit is still $state; retaining recovery files" >&2; exit 1 ;;
    esac
done
cp -p "$snapshot/wpa_supplicant.conf" /etc/wpa_supplicant/wpa_supplicant.conf
for unit in turboexo-dhcp.service turboexo-hostapd.service turboexo-ap0.service; do
    rm -f "/etc/systemd/system/$unit"
done
rm -f /usr/local/libexec/turboexo-ap0
rm -f /etc/turboexo/wifi/hostapd.conf /etc/turboexo/wifi/dnsmasq.conf
systemctl daemon-reload
wpa_cli -i wlan0 reconfigure
wpa_cli -i wlan0 reconnect
logger -t turboexo-wifi 'Prior Wi-Fi configuration restored; hotspot services removed'
