#!/bin/bash
set -euo pipefail

EXPECTED_IMAGE_SHA=16508fbe39d64d7edf3aeffe2500ee79460e72d27d22716076edccb9b98cb81f
EXPECTED_EDID_SHA=97561819e31e20bf315ab863d1f9046d802c6a9a9112b82801664b1cd12aff7c
KERNEL_VERSION=$(uname -r)
ROOT_INITRD="/boot/initrd.img-${KERNEL_VERSION}"
FIRMWARE_INITRD=/boot/firmware/initramfs_2712
CMDLINE=/boot/firmware/cmdline.txt
CONFIG=/boot/firmware/config.txt
THEME_DIR=/usr/share/plymouth/themes/turboexo
EDID=/lib/firmware/edid/turboexo-1920x1280.bin

fail() {
    echo "ERROR: $*" >&2
    exit 1
}

require_file() {
    [[ -f "$1" ]] || fail "missing $1"
}

[[ $KERNEL_VERSION == *-rpi-2712 ]] || fail "unexpected kernel flavour: $KERNEL_VERSION"
[[ $(plymouth-set-default-theme) == turboexo ]] || fail "TurboExo is not the selected Plymouth theme"
grep -Eq '^DeviceScale=1$' /etc/plymouth/plymouthd.conf \
    || fail "Plymouth device scale is not pinned to 1"

for required in \
    "$CONFIG" \
    "$CMDLINE" \
    "$ROOT_INITRD" \
    "$FIRMWARE_INITRD" \
    "$THEME_DIR/turboexo.plymouth" \
    "$THEME_DIR/turboexo.script" \
    "$THEME_DIR/exocet-boot-v10-root.png" \
    "$EDID" \
    /etc/initramfs-tools/hooks/turboexo-edid \
    /etc/systemd/system/plymouth-quit.service.d/turboexo-retain-splash.conf \
    /etc/systemd/system/turboexo-boot-timeline.service \
    /usr/local/libexec/turboexo-boot-timeline.sh; do
    require_file "$required"
done

[[ $(sha256sum "$THEME_DIR/exocet-boot-v10-root.png" | cut -d' ' -f1) == "$EXPECTED_IMAGE_SHA" ]] \
    || fail "installed artwork checksum mismatch"
[[ $(sha256sum "$EDID" | cut -d' ' -f1) == "$EXPECTED_EDID_SHA" ]] \
    || fail "installed EDID checksum mismatch"

python3 - "$THEME_DIR/exocet-boot-v10-root.png" "$EDID" <<'PY'
import struct
import sys

png_path, edid_path = sys.argv[1:]
with open(png_path, "rb") as stream:
    header = stream.read(24)
if header[:8] != b"\x89PNG\r\n\x1a\n":
    raise SystemExit("installed artwork is not PNG")
width, height = struct.unpack(">II", header[16:24])
if (width, height) != (1920, 1280):
    raise SystemExit(f"artwork is {width}x{height}, expected 1920x1280")

with open(edid_path, "rb") as stream:
    edid = stream.read()
if len(edid) != 256:
    raise SystemExit(f"EDID is {len(edid)} bytes, expected 256")
for index in range(0, len(edid), 128):
    if sum(edid[index:index + 128]) % 256:
        raise SystemExit(f"EDID block {index // 128} checksum is invalid")
PY

grep -Eq '^[[:space:]]*auto_initramfs=1([[:space:]]*(#.*)?)?$' "$CONFIG" \
    || fail "auto_initramfs=1 is missing from config.txt"
[[ $(wc -l < "$CMDLINE") -eq 1 ]] || fail "cmdline.txt must contain exactly one line"

for token in \
    splash \
    plymouth.ignore-serial-consoles \
    drm.edid_firmware=HDMI-A-1:edid/turboexo-1920x1280.bin \
    video=HDMI-A-1:1920x1280@60e; do
    count=$(tr ' ' '\n' < "$CMDLINE" | grep -Fxc "$token" || true)
    [[ $count -eq 1 ]] || fail "expected exactly one '$token' token in cmdline.txt, found $count"
done

if tr ' ' '\n' < "$CMDLINE" | grep -Eq '^(nosplash|plymouth.enable=0)$'; then
    fail "cmdline.txt disables Plymouth"
fi

grep -Eq '^INITRAMFS=auto$' /etc/default/raspi-firmware \
    || fail "INITRAMFS=auto is not enabled for kernel upgrades"
grep -Eq '^SKIP_INITRAMFS_GEN=no$' /etc/default/raspi-firmware \
    || fail "future kernel initramfs generation is disabled"

cmp -s "$ROOT_INITRD" "$FIRMWARE_INITRD" \
    || fail "$FIRMWARE_INITRD is not an exact copy of $ROOT_INITRD"

initrd_listing=$(lsinitramfs "$ROOT_INITRD")
for pattern in \
    'usr/sbin/plymouthd' \
    'usr/lib/.*/plymouth/renderers/drm.so' \
    'usr/lib/.*/plymouth/script.so' \
    'usr/share/plymouth/themes/turboexo/turboexo.plymouth' \
    'usr/share/plymouth/themes/turboexo/turboexo.script' \
    'usr/share/plymouth/themes/turboexo/exocet-boot-v10-root.png' \
    'lib/firmware/edid/turboexo-1920x1280.bin' \
    'lib/modules/.*/kernel/drivers/gpu/drm/vc4/vc4\.ko'; do
    grep -Eq "$pattern" <<< "$initrd_listing" || fail "initramfs is missing pattern: $pattern"
done

systemd-analyze verify \
    /usr/lib/systemd/system/plymouth-start.service \
    /usr/lib/systemd/system/plymouth-quit.service \
    /usr/lib/systemd/system/plymouth-quit-wait.service \
    /etc/systemd/system/turboexo-boot-timeline.service
systemctl is-enabled --quiet turboexo-boot-timeline.service \
    || fail "turboexo-boot-timeline.service is not enabled"

boot_kernel=/boot/firmware/kernel_2712.img
require_file "$boot_kernel"
cmp -s "/boot/vmlinuz-${KERNEL_VERSION}" "$boot_kernel" \
    || fail "boot firmware kernel does not match running/latest kernel"

echo "Validated TurboExo Plymouth theme, EDID, systemd units, initramfs, and Pi boot paths."
echo "initramfs: $(stat -c '%s bytes' "$ROOT_INITRD")"
echo "boot copy: $(sha256sum "$FIRMWARE_INITRD" | cut -d' ' -f1)"
