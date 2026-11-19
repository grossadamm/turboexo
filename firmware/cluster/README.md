# ESP32-P4 cluster firmware

Native C++/LVGL firmware for the **4D Systems ESP32-P4-70**, with Street, Track
and Tuning views based on the [accepted mocks](../../dashboard/esp32p4-mocks/README.md).
The physical display is non-touch. Its portrait 800×1280 scanout is rotated to
logical 1280×800; the same Dashboard renderer runs in the host simulator.

## Code boundaries

- `core/` and `include/cluster/` contain the platform-independent protocol,
  telemetry model, exact replay/history, controls and calibration. Host tests
  exercise these contracts independently of ESP-IDF.
- `main/` owns hardware adapters and the application loop. The app is the sole
  writer of display state; UART/ADC snapshots arrive through bounded queues,
  and a separate bounded queue owns SD writes.
- `ui/` is the shared native renderer. `host/` provides deterministic captures
  and the optional SDL window; generated licensed assets are in `assets/`.

## Build dependencies

Use ESP-IDF **v5.5.5**, target `esp32p4`. The component manifest and lockfile pin
4D LCD **0.1.1**, LVGL **9.5.0**, and Espressif LVGL port **2.7.0**, including
resolved transitive drivers. The [board evidence](../../docs/firmware/research/board.md)
explains the exact controller, timing and pins; this is not an interchangeable
Espressif evaluation-board BSP.

Keep dependency clones and installed tools in persistent storage. On this Mac:

```sh
export CLUSTER_DEPS_DIR=/Users/adamgross/TunerStudioProjects/TurboExo-deps
export IDF_TOOLS_PATH="$CLUSTER_DEPS_DIR/esp-idf-tools"
source "$CLUSTER_DEPS_DIR/esp-idf-v5.5.5/export.sh"
export LVGL_SOURCE_DIR="$CLUSTER_DEPS_DIR/lvgl-9.5.0"
```

For another host, choose its own persistent dependency directory, clone ESP-IDF
at v5.5.5 with its submodules, run `install.sh esp32p4`, and clone LVGL at v9.5.0.
Set `CLUSTER_DEPS_DIR` and `LVGL_SOURCE_DIR` accordingly. Host C++17, CMake and
Ninja are required. SDL2 is optional for the interactive window; offscreen
captures do not require a display server. [Setup evidence](../../docs/firmware/research/setup.md)
records the installed versions and the generic P4 probe.

From the repository root, the local gate is:

```sh
./scripts/verify-firmware.sh --host-only
./scripts/verify-firmware.sh
```

The host gate checks the replay source, documentation links, portable core and UART-adapter boundary tests
(with ASan/UBSan on supported host compilers), display-only animation tests,
and actual LVGL captures. The full
gate also builds all four replay/live × pre-v3/v3 profiles in separate build and
sdkconfig paths. It never flashes hardware. Evidence is written under
`.artifacts/firmware/verify/`; `CLUSTER_VERIFY_DIR` selects another persistent
output location. `CLUSTER_IDF_PATH` and `CLUSTER_IDF_TOOLS_PATH` can override the
pinned tool installation locations, not the required version.

To build one profile explicitly (use absolute paths for config/output):

```sh
project_dir="$PWD/firmware/cluster"
build_dir="$PWD/.artifacts/firmware/manual-replay-prev3"
mkdir -p "$build_dir"
idf.py -C "$project_dir" -B "$build_dir/build" \
  -DSDKCONFIG="$build_dir/sdkconfig" \
  -DSDKCONFIG_DEFAULTS="$project_dir/sdkconfig.defaults;$project_dir/sdkconfig.rev-prev3" \
  -DIDF_TARGET=esp32p4 build
```

Use `sdkconfig.rev-v3` for revision 3.0+ and append `;.../sdkconfig.live` for the
live profile. **The supplied live profile enables SD logging and compiles ADS
support.** With a FAT card inserted it creates a log automatically; blank ADC
calibration leaves the I²C bus disabled. To build without card writes, turn off
`TurboExo cluster → Log telemetry to the onboard microSD card` in that build
configuration (`CONFIG_CLUSTER_SD_LOGGING=n`). Use `idf.py menuconfig` with the
same project/build/sdkconfig arguments; existing sdkconfig values take precedence
over defaults. Do not reuse sdkconfig files between profiles. The pre-v3 profile
explicitly selects minimum revision 0; the v3 profile selects minimum 3.0
instead of the SDK default 3.1. **Identify the delivered silicon and board
revision before choosing an image to flash.** No hardware is accessed by these
builds.

## Controls and startup

Three external active-low buttons to ground use internal pull-ups:

| Button | GPIO / H4 pin | Behavior |
| --- | --- | --- |
| Mode | 19 / 21 | Short press cycles Street → Track → Tuning |
| Brightness | 20 / 22 | Cycles backlight levels |
| Replay | 21 / 19 | Pauses/resumes replay; does not send ECU commands |

Mode and brightness preferences are saved after changes settle, not every frame.
Native default is Street; saved mode takes precedence. BOOT and RESET on the
module remain service/recovery controls. `CONFIG_CLUSTER_PANEL_ROTATE_270`
selects the alternative landscape mounting orientation.

The default build is **replay** with an on-screen replay indication. It uses the
accepted 54.425-second October 23 clip and explicitly simulated speed, fuel and
oil temperature. These synthetic values never feed a live build. Replay loops
clear history only after presenting the final recorded sample; pausing freezes
the presentation clock. Tuning history consumes the original source rows in
order, including different measurements that share a timestamp, rather than
resampling them at display-frame frequency.

A live build starts **AwaitEcuReset on every boot**. Reset the ECU under the
bench procedure, then hold Mode for two seconds to confirm that reset and enable
communication. This is an operator action for the legacy serial parser, not a
build-approval prompt. The ECU's legacy parser can wait indefinitely for an
interrupted command; restarting only the dash does not reset it. An uncertain or
partial UART transmission returns to an inhibited fault and requires another
actual ECU reset and confirmation. No automatic NUL-padding recovery is used.

## ECU connection and data qualification

The dedicated UART1 runs 115200 8N1 on **P4 GPIO17 TX / GPIO18 RX**, H4 pins
23/24. H4 pins 3/4 provide signal ground. USB-PROG is for console/debugging;
console text never goes to the ECU UART.

On the researched **UA4C vC5 P4 SER3** connector, pin 1 is ECU TX3, pin 2 RX3,
pin 3 ground, and pin 4 the 5 V rail. Cross TX/RX through verified **5 V ↔ 3.3 V
logic translation**, share signal ground, and leave ECU pin 4 unconnected when
the display has its own supply. Confirm the installed board revision, connector
orientation, jumpers and levels before connecting. See the
[protocol and schematic evidence](../../docs/firmware/research/protocol.md).

An operator must enable the actual ECU secondary serial interface in
**Generic (ini File)** mode and verify its operation after restart. The dash
never changes those settings. Enabling secondary serial changes which Aux input
mode bits Speeduino uses: verify Aux0 remains the analog A8 Spartan-status input,
review other active Aux modes, and preserve oil pressure on dedicated A9.

The client accepts only exact `S` identities for 202501, 202501.6 or 202501.7,
then sends two fixed `r` spans (0–43 and 76–108) at a maximum of five complete
cycles per second. Each reply must have its exact header and length and pass a
quiet guard before advancing. The adapter samples the RX line, receiver FSM,
hardware FIFO, driver ring and queued errors; its ISR and worker share a core
so a byte in transit between hardware and software cannot masquerade as quiet.
Only a complete cycle is published. There is no
CRC in this legacy protocol and the two spans are not an atomic ECU snapshot.
The implementation sends no tuning commands or arbitrary serial payloads.

Transport freshness, sensor qualification and ECU protection flags are separate:

- Data older than 1,000 ms becomes unavailable, including history gaps. A bad
  sensor field does not suppress unrelated readings or ECU protection flags.
- `CONFIG_CLUSTER_ECU_VSS` enables a verified ECU speed source. Wire km/h becomes
  displayed mph. A disabled/unconfigured source is not interpreted as measured
  zero.
- `CONFIG_CLUSTER_ECU_OIL_PRESSURE` enables a verified oil-pressure source.
  Raw sensor calibration and hardware operation still require bench comparison.
- Tuning's raw AFR is diagnostic while readiness is unverified. The reported
  target is withheld through a conservative observed-running startup interval
  of configured EGO delay plus one second, reset by stop, crank, sync loss or
  stale/reconnected data. The ECU uptime byte is not its runSecs timer.
- Boost is MAP minus barometric pressure converted to psi; it retains vacuum's
  negative sign. Gauge bounds are display limits, not warning or operating
  limits. Numeric out-of-range readings are not silently clamped to the bar.

## Optional fuel and oil-temperature inputs

The external ADS1115 path uses I²C1, GPIO15 SDA / GPIO16 SCL (H4 pins 25/26),
address 0x48, A0 fuel and A1 oil temperature. Use 3.3 V bus levels and verify
actual pull-ups and the carrier pin map. The old Pi stacking connector is not a
P4 connector. [Sender and carrier evidence](../../docs/firmware/research/sensors.md)
records the known parts and remaining calibration work.

Enable `CONFIG_CLUSTER_ADS1115` and supply measured calibration in
`CONFIG_CLUSTER_ADS1115_FUEL_KNOTS` and/or
`CONFIG_CLUSTER_ADS1115_OIL_TEMP_KNOTS`. Format is comma-separated `raw:value`
pairs, 2–16 knots in ascending raw ADC counts. Raw counts use single-ended
ADS1115 conversions at ±4.096 V full scale and 128 samples/s. Fuel values are
percent; oil-temperature values are °F. Enter measured points for the actual
sender, bias network and ADC configuration; no factory-looking placeholder
curve is installed.

Empty or invalid profiles leave engineering readings unavailable. A channel
outside its measured count range is unavailable rather than extrapolated.
The bus stays disabled when no valid profile is supplied. Enabled bus failures
invalidate the affected readings without blocking telemetry or display work.

## Optional microSD logging

`CONFIG_CLUSTER_SD_LOGGING` mounts an existing FAT card without formatting it.
A separate bounded writer queue keeps mount/write/flush latency out of the UI and
UART paths. Log names are unique per session; timestamps are relative monotonic
time, not fabricated calendar dates. `boot_ms` is the process clock; replay
`received_ms` and per-value observation timestamps use its pause-adjusted
presentation clock. CSV rows carry per-value quality so raw,
missing and simulated inputs remain distinguishable. These are comma-delimited
cluster records, not TunerStudio MLG files or its semicolon-separated exports.

The screen indicates recording or logging errors/drops. Fresh local ADC
observations and validity changes are logged even while the ECU link is offline
or disarmed. Card absence, removal,
or a write failure does not stop gauges. Logging does not automatically remount
a removed or newly inserted card; start a new device session after correcting
the card issue. Flushes reduce the loss window but do
not guarantee filesystem or final-row durability during a power cut. Verify the
specific card and power behavior before relying on logs in the car.

## Validation and physical acceptance

The local gate demonstrates compilation, portable logic behavior and native UI
layout. It does not demonstrate actual display timing, automotive power behavior
or live ECU compatibility. Before replacing the Pi:

1. Identify chip/PCB revision, power arrangement and the correct firmware image.
2. Verify landscape orientation, RGB565 colors, brightness controls, boot time,
   frame pacing, tearing and operation through the intended power sequence.
3. Verify translated UART levels and exact request bytes; confirm secondary
   mode and Aux input assignments in TunerStudio.
4. Compare live channel values with USB TunerStudio simultaneously. Check loop
   rate and sync-loss counters with the dash connected/disconnected at key-on and
   stationary idle before changing the polling rate.
5. Validate speed, oil pressure and external sender calibration; exercise
   disconnect/reconnect, reset acknowledgment and sensor failure indications.
6. Confirm controls, saved preferences, card absence/full/removal behavior and
   the intended key-off logging/power arrangement.

No live-device acceptance result is implied by the checked-in source or host
screenshots. Source evidence and exact version pins are maintained under
[docs/firmware/research](../../docs/firmware/research/board.md).
