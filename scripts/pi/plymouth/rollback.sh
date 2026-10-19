#!/bin/bash
set -euo pipefail

STATE_DIR=/var/lib/turboexo-early-splash
BACKUP_BASE=/var/backups/turboexo-early-splash

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ $EUID -eq 0 ]] || fail "run as root"

backup_id=${1:-}
if [[ -z $backup_id && -f $STATE_DIR/active-backup ]]; then
    backup_id=$(<"$STATE_DIR/active-backup")
fi
[[ -n $backup_id ]] || fail "pass a backup ID or restore the active-backup state file"
[[ $backup_id != */* ]] || fail "invalid backup ID"

backup_root="$BACKUP_BASE/$backup_id"
[[ -d $backup_root ]] || fail "backup does not exist: $backup_root"

restore_path() {
    local target=$1
    local relative=${target#/}
    if [[ -e "$backup_root/absent/$relative" ]]; then
        rm -rf -- "$target"
    elif [[ -e "$backup_root/files/$relative" || -L "$backup_root/files/$relative" ]]; then
        rm -rf -- "$target"
        mkdir -p "$(dirname "$target")"
        cp -a "$backup_root/files/$relative" "$target"
    else
        fail "backup has no state for $target"
    fi
}

systemctl disable turboexo-boot-timeline.service 2>/dev/null || true

# Restore boot-critical files first. Once these are synced, the Pi will bypass
# the added initramfs and Plymouth even if later root-filesystem cleanup fails.
restore_path /boot/firmware/config.txt
restore_path /boot/firmware/cmdline.txt
restore_path /boot/firmware/initramfs_2712

# The original system had no Plymouth package. It remains installed after this
# reversible rollback, so explicitly prevent its root-filesystem systemd units
# from starting until package cleanup is intentionally performed.
read -r restored_cmdline < /boot/firmware/cmdline.txt
case " $restored_cmdline " in
    *' plymouth.enable=0 '*) ;;
    *) printf '%s plymouth.enable=0\n' "$restored_cmdline" > /boot/firmware/cmdline.txt ;;
esac
sync /boot/firmware

for target in \
    /etc/default/raspi-firmware \
    /etc/initramfs-tools/modules \
    /etc/initramfs-tools/hooks/turboexo-edid \
    /etc/plymouth/plymouthd.conf \
    /usr/share/plymouth/themes/default.plymouth \
    /usr/share/plymouth/themes/turboexo \
    /lib/firmware/edid/turboexo-1920x1280.bin \
    /etc/systemd/system/plymouth-quit.service.d/turboexo-retain-splash.conf \
    /etc/systemd/system/turboexo-boot-timeline.service \
    /etc/systemd/system/multi-user.target.wants/turboexo-boot-timeline.service \
    /usr/local/libexec/turboexo-boot-timeline.sh \
    /usr/local/sbin/turboexo-plymouth-validate \
    /usr/local/sbin/turboexo-plymouth-rollback \
    "/boot/initrd.img-$(uname -r)" \
    "$STATE_DIR/active-backup"; do
    restore_path "$target"
done

systemctl daemon-reload
sync

echo "Restored TurboExo early-splash backup $backup_id."
echo "Plymouth packages were left installed and disabled with plymouth.enable=0."
echo "No reboot was performed."
