#!/bin/bash
set -euo pipefail

readonly SOURCE_URL="https://github.com/Pi4J/pi4j-v1/archive/9f12d65a529d4de7e646eb210a3f4884f19503c0.tar.gz"
readonly SOURCE_SHA256="c91c8978943bed8a09f72d5b5078dfff19aacd6e189b77f15d076346392372f5"
readonly DEST_DIR="/usr/local/lib/turboexo-pi4j"
readonly DEST="$DEST_DIR/libpi4j.so"
readonly SERVICE_USER="dietpi"
readonly SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)

if [[ $(id -u) -ne 0 ]]; then
    echo "Run as root." >&2
    exit 2
fi
if [[ $(uname -m) != aarch64 ]]; then
    echo "Unsupported architecture: $(uname -m) (expected aarch64)" >&2
    exit 2
fi
for command in curl gcc gpio install javac ldd make patch readelf sha256sum tar usermod; do
    command -v "$command" >/dev/null || {
        echo "Missing required command: $command" >&2
        exit 2
    }
done

temporary=$(mktemp -d /tmp/turboexo-pi4j-build.XXXXXX)
trap 'rm -rf -- "$temporary"' EXIT
archive="$temporary/pi4j-v1.tar.gz"
source_dir="$temporary/source"

curl -fsSLo "$archive" "$SOURCE_URL"
printf '%s  %s\n' "$SOURCE_SHA256" "$archive" | sha256sum --check --status
mkdir "$source_dir"
tar -xzf "$archive" -C "$source_dir" --strip-components=1
patch -d "$source_dir" -p1 < "$SCRIPT_DIR/pi4j-1.4-pi5-sysfs-base.patch"

java_home=$(dirname "$(dirname "$(readlink -f "$(command -v javac)")")")
native_dir="$source_dir/pi4j-native/src/main/native"
# WiringPi 3.16 still exports the legacy waitForInterrupt symbol but no longer
# declares it in the public header. Pi4J v1 references it outside our GPIO path.
make -C "$native_dir" dynamic JAVA_HOME="$java_home" \
    CARGS="-fcommon -Wno-error=implicit-function-declaration"

bridge="$native_dir/libpi4j.so"
readelf -h "$bridge" | grep -q 'Machine:.*AArch64'
ldd -r "$bridge" | grep -q 'libwiringPi.so'
gpio -v | grep -q 'Type: Pi 5'

install -d -m 0755 "$DEST_DIR"
install -m 0755 "$bridge" "$DEST"
usermod -a -G gpio "$SERVICE_USER"

printf 'Installed %s\n' "$DEST"
printf 'Added %s to the gpio group; start a new session before testing.\n' "$SERVICE_USER"
