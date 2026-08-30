#!/bin/bash
set -euo pipefail

readonly RUNTIME_DIR="/run/turboexo-key-input"
readonly ENVIRONMENT_FILE="$RUNTIME_DIR/environment"
readonly LOGICAL_BCM=17

if [[ $(id -u) -ne 0 ]]; then
    echo "Run as root." >&2
    exit 2
fi

mkdir -p /sys/kernel/debug
if ! mountpoint -q /sys/kernel/debug; then
    mount -t debugfs debugfs /sys/kernel/debug
fi

# Raspberry Pi's current kernel does not build gpio-sim, but it does provide the
# maintained gpio-mockup compatibility module. Use a dynamically allocated
# one-line chip; neither its gpiochip index nor legacy sysfs base is stable.
modprobe gpio-mockup gpio_mockup_ranges=-1,1 gpio_mockup_named_lines=1

chip_directory=""
for candidate in /sys/class/gpio/gpiochip*; do
    [[ -r "$candidate/label" ]] || continue
    if [[ $(<"$candidate/label") == gpio-mockup-* ]]; then
        chip_directory=$candidate
        break
    fi
done
if [[ -z "$chip_directory" ]]; then
    echo "Unable to discover gpio-mockup chip." >&2
    exit 1
fi

sysfs_gpio=$(<"$chip_directory/base")
chip_target=$(readlink -f "$chip_directory")
platform_device=$(dirname "$(dirname "$chip_target")")
kernel_chip=""
for candidate in /sys/bus/gpio/devices/gpiochip*; do
    candidate_target=$(readlink -f "$candidate")
    if [[ $(dirname "$candidate_target") == "$platform_device" ]]; then
        kernel_chip=$(basename "$candidate")
        break
    fi
done
if [[ -z "$kernel_chip" ]]; then
    echo "Unable to map gpio-mockup sysfs chip to its kernel chip." >&2
    exit 1
fi
pull_path="/sys/kernel/debug/gpio-mockup/$kernel_chip/0"
if [[ ! -f "$pull_path" ]]; then
    echo "Unable to discover gpio-mockup pull control: $pull_path" >&2
    exit 1
fi

chgrp gpio "$pull_path"
chmod 0660 "$pull_path"
install -d -o root -g gpio -m 0775 "$RUNTIME_DIR"
if mountpoint -q "$RUNTIME_DIR/pull"; then
    umount "$RUNTIME_DIR/pull"
fi
if [[ -L "$RUNTIME_DIR/pull" ]]; then
    unlink "$RUNTIME_DIR/pull"
fi
install -o root -g gpio -m 0660 /dev/null "$RUNTIME_DIR/pull"
mount --bind "$pull_path" "$RUNTIME_DIR/pull"

# Default high prevents TSDash from pre-qualifying key-off before the monitor's
# first I2C sample. A first valid discharging sample still replaces it with low;
# invalid samples leave the safe startup value unchanged.
printf '1\n' > "$RUNTIME_DIR/pull"

temporary=$(mktemp "$RUNTIME_DIR/environment.XXXXXX")
trap 'rm -f -- "$temporary"' EXIT
cat > "$temporary" <<EOF
PI4J_VIRTUAL_BCM=$LOGICAL_BCM
PI4J_VIRTUAL_SYSFS_GPIO=$sysfs_gpio
TURBOEXO_KEY_STATE_PATH=$RUNTIME_DIR/pull
EOF
chown root:gpio "$temporary"
chmod 0640 "$temporary"
mv -f "$temporary" "$ENVIRONMENT_FILE"
trap - EXIT

printf 'Virtual key input ready: BCM %d -> sysfs GPIO %d\n' \
    "$LOGICAL_BCM" "$sysfs_gpio"
