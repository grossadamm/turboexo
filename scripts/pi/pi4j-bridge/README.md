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
API on the Pi 5 without modifying TSDash's JARs or migrating its Java code.
The intended application is to publish the car's existing key-on voltage signal
as a TSDash input channel. The bridge does not switch power, drive the UPS/J2
power-button circuit, or configure any GPIO output.

## Install and test

```bash
sudo ./install.sh

javac -cp /home/dietpi/TSDash/lib/pi4j-core.jar GpioInputProbe.java
java -Dpi4j.library.path=/usr/local/lib/turboexo-pi4j \
  -cp .:/home/dietpi/TSDash/lib/pi4j-core.jar GpioInputProbe 17
```

The probe expects an unclaimed, unwired GPIO17 and verifies that it follows its
internal pull-up and pull-down. It restores the pull setting to off before exit.

TSDash is pointed at the bridge by exporting these before its Java process starts:

```bash
JAVA_TOOL_OPTIONS=-Dpi4j.library.path=/usr/local/lib/turboexo-pi4j
PI4J_GPIO_SYSFS_BASE=<RP1 gpiochip sysfs base>
```

GPIO17 is used only as an unclaimed bench-test pin by the included probes. It is
not a production assignment, and no TSDash pin function is installed by this
bridge.

## Verified result

- `dietpi` can load the patched aarch64 JNI library as a non-root `gpio` member.
- `GpioInputProbe` reads internal pull-up `1` and pull-down `0` on GPIO17.
- `GpioControllerProbe` provisions GPIO17 through Pi4J's high-level provider and
  reads `HIGH`.
- TSDash Pin Management starts without `ELFCLASS32`, native-method, or legacy
  sysfs-numbering errors.
- The temporary `KeyOnInput` used to validate TSDash was deleted afterward.

## Rollback

Remove the `JAVA_TOOL_OPTIONS` and `PI4J_GPIO_SYSFS_BASE` exports from the
launcher and restart TSDash. The isolated library can remain installed while
unused.
