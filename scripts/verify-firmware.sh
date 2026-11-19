#!/usr/bin/env bash
# Repository-local firmware gate. Never flashes hardware or formats/removes data.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROJECT="$ROOT/firmware/cluster"
COMMON_GIT="$(git -C "$ROOT" rev-parse --path-format=absolute --git-common-dir)"
DEPS="${CLUSTER_DEPS_DIR:-$(dirname "$COMMON_GIT")-deps}"
OUT="${CLUSTER_VERIFY_DIR:-$ROOT/.artifacts/firmware/verify}"
HOST_ONLY=false
if [[ "${1:-}" == '--host-only' ]]; then
  HOST_ONLY=true
elif [[ $# -ne 0 ]]; then
  echo 'Usage: scripts/verify-firmware.sh [--host-only]' >&2
  exit 2
fi
mkdir -p "$OUT/logs" "$OUT/configs" "$OUT/captures"
run_step() {
  local name="$1"
  shift
  echo "Checking $name"
  if ! "$@" >"$OUT/logs/$name.log" 2>&1; then
    tail -n 80 "$OUT/logs/$name.log" >&2
    echo "Failed: $name ($OUT/logs/$name.log)" >&2
    return 1
  fi
}

if [[ "$HOST_ONLY" == false ]]; then
  export IDF_PATH="${CLUSTER_IDF_PATH:-$DEPS/esp-idf-v5.5.5}"
  export IDF_TOOLS_PATH="${CLUSTER_IDF_TOOLS_PATH:-$DEPS/esp-idf-tools}"
  if [[ ! -f "$IDF_PATH/export.sh" ]]; then
    echo "Missing pinned ESP-IDF: $IDF_PATH. See firmware/cluster/README.md." >&2
    exit 1
  fi
  # ESP-IDF's export script manages environment variables that can be unset.
  set +u
  source "$IDF_PATH/export.sh" >"$OUT/logs/idf-environment.log" 2>&1
  set -u
  idf.py --version | tee "$OUT/logs/idf-version.log"
  if ! grep -q 'v5.5.5' "$OUT/logs/idf-version.log"; then
    echo 'ESP-IDF v5.5.5 is required.' >&2
    exit 1
  fi
fi

LVGL_SOURCE_DIR="${LVGL_SOURCE_DIR:-$DEPS/lvgl-9.5.0}"
if [[ ! -f "$LVGL_SOURCE_DIR/CMakeLists.txt" ]]; then
  echo "Missing LVGL 9.5.0 source: $LVGL_SOURCE_DIR. See firmware/cluster/README.md." >&2
  exit 1
fi
run_step replay-source python3 "$PROJECT/tools/generate_replay.py" --check
run_step docs python3 "$PROJECT/tools/check_docs.py"
run_step core-configure cmake -S "$PROJECT/tests" -B "$OUT/core" -G Ninja -DCLUSTER_SANITIZE=ON
run_step core-build cmake --build "$OUT/core" --parallel 4
run_step core-tests ctest --test-dir "$OUT/core" --output-on-failure
run_step ui-configure cmake -S "$PROJECT/host" -B "$OUT/host" -G Ninja -DLVGL_SOURCE_DIR="$LVGL_SOURCE_DIR"
run_step ui-build cmake --build "$OUT/host" --parallel 4
run_step ui-tests ctest --test-dir "$OUT/host" --output-on-failure
run_step ui-captures "$OUT/host/cluster_sim" --capture-dir "$OUT/captures"
run_step ui-png python3 "$PROJECT/tools/ppm_to_png.py" "$OUT/captures"

if [[ "$HOST_ONLY" == false ]]; then
  for revision in prev3 v3; do
    for source in replay live; do
      profile="$source-$revision"
      defaults="$PROJECT/sdkconfig.defaults;$PROJECT/sdkconfig.rev-$revision"
      if [[ "$source" == live ]]; then defaults="$defaults;$PROJECT/sdkconfig.live"; fi
      run_step "idf-$profile" idf.py -C "$PROJECT" -B "$OUT/idf-$profile" \
        -DSDKCONFIG="$OUT/configs/$profile" -DSDKCONFIG_DEFAULTS="$defaults" \
        -DIDF_TARGET=esp32p4 build
      python3 - "$OUT/configs/$profile" "$revision" "$source" <<'PY'
import sys
from pathlib import Path
config = Path(sys.argv[1]).read_text()
expected_revision = '0' if sys.argv[2] == 'prev3' else '300'
required = [f'CONFIG_ESP32P4_REV_MIN_FULL={expected_revision}', 'CONFIG_ESP32P4_LCD_70=y',
            'CONFIG_ESP32P4_LCD_NOTOUCH=y', 'CONFIG_ESP_CONSOLE_USB_SERIAL_JTAG=y']
if sys.argv[3] == 'live':
    required += ['CONFIG_CLUSTER_LIVE=y', 'CONFIG_CLUSTER_ADS1115=y', 'CONFIG_CLUSTER_SD_LOGGING=y']
else:
    required += ['# CONFIG_CLUSTER_LIVE is not set']
for setting in required:
    if setting not in config.splitlines():
        raise SystemExit(f'{sys.argv[1]}: expected {setting}')
PY
    done
  done
fi
printf 'Firmware gate passed. Evidence: %s\n' "$OUT"
