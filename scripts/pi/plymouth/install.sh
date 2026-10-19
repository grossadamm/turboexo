#!/bin/bash
set -euo pipefail

EXPECTED_IMAGE_SHA=16508fbe39d64d7edf3aeffe2500ee79460e72d27d22716076edccb9b98cb81f
EXPECTED_EDID_SHA=97561819e31e20bf315ab863d1f9046d802c6a9a9112b82801664b1cd12aff7c
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd -- "$SCRIPT_DIR/../../.." && pwd)
ARTWORK="$REPO_ROOT/assets/boot/exocet-boot-v10-root.png"
CONFIG=/boot/firmware/config.txt
CMDLINE=/boot/firmware/cmdline.txt
KERNEL_VERSION=$(uname -r)
ROOT_INITRD="/boot/initrd.img-${KERNEL_VERSION}"
FIRMWARE_INITRD=/boot/firmware/initramfs_2712
BACKUP_ID=$(date -u +%Y%m%dT%H%M%SZ)
BACKUP_ROOT="/var/backups/turboexo-early-splash/${BACKUP_ID}"
BOOT_ROLLBACK="/boot/firmware/turboexo-rollback/${BACKUP_ID}"
STATE_DIR=/var/lib/turboexo-early-splash

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

[[ $EUID -eq 0 ]] || fail "run as root"
[[ $(hostname) == DietPi ]] || fail "expected hostname DietPi"
[[ $(dpkg --print-architecture) == arm64 ]] || fail "expected arm64"
[[ $(tr -d '\0' </proc/device-tree/model) == 'Raspberry Pi 5 Model B Rev 1.0' ]] \
    || fail "expected the verified Raspberry Pi 5"
[[ $KERNEL_VERSION == *-rpi-2712 ]] || fail "unexpected kernel flavour: $KERNEL_VERSION"
[[ $(. /etc/os-release; echo "$VERSION_CODENAME") == trixie ]] || fail "expected Debian trixie"
mountpoint -q /boot/firmware || fail "/boot/firmware is not mounted"
boot_fstype=$(stat -f -c %T /boot/firmware)
[[ $boot_fstype == msdos || $boot_fstype == vfat ]] || fail "/boot/firmware is not FAT"
[[ -f $CONFIG && -f $CMDLINE ]] || fail "Pi boot configuration is missing"
[[ $(wc -l < "$CMDLINE") -eq 1 ]] || fail "cmdline.txt must contain exactly one line"
[[ -f $ARTWORK ]] || fail "missing repository artwork: $ARTWORK"
[[ ! -e $STATE_DIR/active-backup ]] || fail "an early-splash installation is already active; roll it back first"
[[ $(sha256sum "$ARTWORK" | cut -d' ' -f1) == "$EXPECTED_IMAGE_SHA" ]] \
    || fail "repository artwork checksum mismatch"

tmp_dir=$(mktemp -d /tmp/turboexo-early-splash.XXXXXX)
trap 'rm -rf "$tmp_dir"' EXIT
base64 -d "$SCRIPT_DIR/turboexo-display.edid.base64" > "$tmp_dir/turboexo-1920x1280.bin"
[[ $(sha256sum "$tmp_dir/turboexo-1920x1280.bin" | cut -d' ' -f1) == "$EXPECTED_EDID_SHA" ]] \
    || fail "repository EDID checksum mismatch"

if [[ -r /sys/class/drm/card1-HDMI-A-1/edid ]] \
        && (( $(wc -c < /sys/class/drm/card1-HDMI-A-1/edid) > 0 )); then
    live_edid_sha=$(sha256sum /sys/class/drm/card1-HDMI-A-1/edid | cut -d' ' -f1)
    [[ $live_edid_sha == "$EXPECTED_EDID_SHA" ]] \
        || fail "connected HDMI-A-1 EDID differs from the verified TurboExo display"
fi

mkdir -p "$BACKUP_ROOT/files" "$BACKUP_ROOT/absent" "$BOOT_ROLLBACK"

backup_path() {
    local target=$1
    local relative=${target#/}
    if [[ -e $target || -L $target ]]; then
        mkdir -p "$BACKUP_ROOT/files/$(dirname "$relative")"
        cp -a "$target" "$BACKUP_ROOT/files/$relative"
        printf 'present %s\n' "$target" >> "$BACKUP_ROOT/manifest"
    else
        mkdir -p "$BACKUP_ROOT/absent/$(dirname "$relative")"
        : > "$BACKUP_ROOT/absent/$relative"
        printf 'absent %s\n' "$target" >> "$BACKUP_ROOT/manifest"
    fi
}

for target in \
    "$CONFIG" \
    "$CMDLINE" \
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
    "$ROOT_INITRD" \
    "$FIRMWARE_INITRD" \
    "$STATE_DIR/active-backup"; do
    backup_path "$target"
done

dpkg-query -W -f='${binary:Package}\t${Version}\t${db:Status-Abbrev}\n' \
    plymouth plymouth-themes 2>/dev/null > "$BACKUP_ROOT/package-state" || true
if command -v plymouth-set-default-theme >/dev/null 2>&1; then
    plymouth-set-default-theme > "$BACKUP_ROOT/previous-theme" || true
else
    : > "$BACKUP_ROOT/previous-theme"
fi

cp -a "$CONFIG" "$BOOT_ROLLBACK/config.txt"
cp -a "$CMDLINE" "$BOOT_ROLLBACK/cmdline.original.txt"
read -r rollback_cmdline < "$CMDLINE"
printf '%s plymouth.enable=0\n' "$rollback_cmdline" > "$BOOT_ROLLBACK/cmdline.txt"
cat > "$BOOT_ROLLBACK/ROLLBACK.txt" <<EOF
TurboExo early-splash offline rollback (${BACKUP_ID})

1. Power the Pi off and mount its FAT boot partition on another computer.
2. Copy this directory's config.txt and cmdline.txt to the root of that FAT
   partition, replacing the active files.
3. Safely unmount the partition and boot the Pi.

The rollback cmdline adds plymouth.enable=0 because the Plymouth package remains
installed on the root filesystem. Restoring these two files disables initramfs
loading, Plymouth, the EDID override, and the forced connector mode. The exact
original is cmdline.original.txt and is also in ${BACKUP_ROOT}; do not use it for
the first recovery boot. Root-filesystem cleanup can wait until SSH is available.
EOF
sync /boot/firmware

echo "Backed up every target before modification: $BACKUP_ROOT"
echo "Offline boot rollback: $BOOT_ROLLBACK"

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends plymouth plymouth-themes

install -d -m 0755 /usr/share/plymouth/themes/turboexo
install -m 0644 "$SCRIPT_DIR/turboexo.plymouth" \
    /usr/share/plymouth/themes/turboexo/turboexo.plymouth
install -m 0644 "$SCRIPT_DIR/turboexo.script" \
    /usr/share/plymouth/themes/turboexo/turboexo.script
install -m 0644 "$ARTWORK" \
    /usr/share/plymouth/themes/turboexo/exocet-boot-v10-root.png
install -m 0644 "$SCRIPT_DIR/plymouthd.conf" /etc/plymouth/plymouthd.conf

install -D -m 0644 "$tmp_dir/turboexo-1920x1280.bin" \
    /lib/firmware/edid/turboexo-1920x1280.bin
install -D -m 0755 "$SCRIPT_DIR/turboexo-edid.initramfs-hook" \
    /etc/initramfs-tools/hooks/turboexo-edid
install -D -m 0644 "$SCRIPT_DIR/plymouth-quit-retain-splash.conf" \
    /etc/systemd/system/plymouth-quit.service.d/turboexo-retain-splash.conf
install -D -m 0755 "$SCRIPT_DIR/turboexo-boot-timeline.sh" \
    /usr/local/libexec/turboexo-boot-timeline.sh
install -D -m 0644 "$SCRIPT_DIR/turboexo-boot-timeline.service" \
    /etc/systemd/system/turboexo-boot-timeline.service
install -D -m 0755 "$SCRIPT_DIR/validate.sh" \
    /usr/local/sbin/turboexo-plymouth-validate
install -D -m 0755 "$SCRIPT_DIR/rollback.sh" \
    /usr/local/sbin/turboexo-plymouth-rollback

set_config_key() {
    local config_file=$1
    local key=$2
    local value=$3
    python3 - "$config_file" "$key" "$value" <<'PY'
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
key = sys.argv[2]
value = sys.argv[3]
lines = path.read_text().splitlines()
pattern = re.compile(rf"^\s*#?\s*{re.escape(key)}\s*=.*$")
replacement = f"{key}={value}"
found = False
output = []
for line in lines:
    if pattern.match(line):
        if not found:
            output.append(replacement)
            found = True
        continue
    output.append(line)
if not found:
    output.extend(["", replacement])
path.write_text("\n".join(output) + "\n")
PY
}

set_config_key /etc/default/raspi-firmware INITRAMFS auto
set_config_key /etc/default/raspi-firmware SKIP_INITRAMFS_GEN no
set_config_key "$CONFIG" auto_initramfs 1

read -r -a old_cmdline < "$CMDLINE"
new_cmdline=()
for token in "${old_cmdline[@]}"; do
    case "$token" in
        splash|plymouth.ignore-serial-consoles|drm.edid_firmware=*|video=HDMI-A-1:*)
            ;;
        *)
            new_cmdline+=("$token")
            ;;
    esac
done
new_cmdline+=(
    splash
    plymouth.ignore-serial-consoles
    drm.edid_firmware=HDMI-A-1:edid/turboexo-1920x1280.bin
    video=HDMI-A-1:1920x1280@60e
)
printf '%s\n' "${new_cmdline[*]}" > "$CMDLINE"

plymouth-set-default-theme turboexo
systemctl daemon-reload
systemctl enable turboexo-boot-timeline.service

if [[ -f $ROOT_INITRD ]]; then
    update-initramfs -u -k "$KERNEL_VERSION"
else
    update-initramfs -c -k "$KERNEL_VERSION"
fi

mkdir -p "$STATE_DIR"
printf '%s\n' "$BACKUP_ID" > "$STATE_DIR/active-backup"
sync /boot/firmware

/usr/local/sbin/turboexo-plymouth-validate

echo "Installation validated. No reboot was performed."
echo "Technical reboot command when ready: systemctl reboot --force"
