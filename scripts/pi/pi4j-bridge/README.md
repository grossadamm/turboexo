# TSDash Pi 5 GPIO bridge

TSDash bundles Pi4J 1.3 and a 32-bit `libpi4j.so`. On the Pi 5's aarch64 JVM,
that embedded library fails with `ELFCLASS32`. Pi4J 1.3 supports an explicit
native-library directory, so TSDash can retain its existing Java API while using
a locally built Pi4J 1.4 aarch64 JNI library and the installed Pi-5-capable
WiringPi 3.16.

The patch also translates Pi4J v1's legacy sysfs GPIO numbering through the
RP1 gpiochip's runtime base. The launcher publishes that base as
`PI4J_GPIO_SYSFS_BASE`; it must not be hard-coded because legacy global GPIO
numbers depend on gpiochip enumeration.

The bridge is intentionally narrow: it restores TSDash's existing Pi4J-v1 GPIO
API on the Pi 5 without modifying TSDash's JARs or migrating its Java code. One
environment-configured logical input can be redirected to a simulated sysfs GPIO;
every other pin retains the RP1 mapping. The bridge never switches power or
touches the UPS/J2 power-button circuit.

## Install and test

From `scripts/pi`, install the bridge, virtual input, monitor integration, and
systemd ordering together:

```bash
sudo ./install-key-input.sh --restart-dashboard
python3 -m unittest test_pi_ups_monitor.py
```

TSDash is pointed at the bridge by exporting these before its Java process starts:

```bash
JAVA_TOOL_OPTIONS=-Dpi4j.library.path=/usr/local/lib/turboexo-pi4j
PI4J_GPIO_SYSFS_BASE=<RP1 gpiochip sysfs base>
PI4J_VIRTUAL_BCM=17
PI4J_VIRTUAL_SYSFS_GPIO=<gpio-mockup runtime sysfs base>
```

The current Raspberry Pi kernel has `CONFIG_GPIO_SIM` disabled and
`CONFIG_GPIO_MOCKUP=m`. `turboexo-key-input.service` therefore creates a one-line
`gpio-mockup` chip, discovers both dynamic identifiers, and bind-mounts its pull
control at `/run/turboexo-key-input/pull`. The Python UPS monitor publishes `1`
for connected and `0` for discharging. Invalid I2C samples leave the last value
unchanged.

TSDash uses logical `GPIO 17`, active-high, pull resistance `OFF`, and publishes
the unique channel `AppEvent.ignitionOn`. The simulated line defaults high so
TSDash cannot pre-qualify a false key-off before the monitor's first sample. The
physical RP1 GPIO17 is never exported or configured.

## Verified result

- `dietpi` can load the patched aarch64 JNI library as a non-root `gpio` member.
- `GpioInputProbe` reads internal pull-up `1` and pull-down `0` on GPIO17.
- `GpioControllerProbe` provisions virtual GPIO17 through Pi4J's high-level
  provider and reads both `LOW` and `HIGH`.
- `GpioControllerEventProbe` receives live `LOW` and `HIGH` callbacks in one JVM.
- TSDash Pin Management starts without `ELFCLASS32`, native-method, or legacy
  sysfs-numbering errors.
- Physical RP1 GPIO17 remains untouched.
- TSDash exposes `AppEvent.ignitionOn`; driving it low closes the active log
  through TSDash's native stop action without restarting the dashboard.

## Rollback

Disable `turboexo-key-input.service`, remove the `KeyOnInput` function in TSDash,
remove the virtual environment loading from the launcher, and restart tty1. The
isolated library may remain installed while unused.
