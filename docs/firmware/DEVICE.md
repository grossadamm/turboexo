# Delivered ESP32-P4 cluster

## Current image — icon/label correction, 2026-11-19

Installed profile: **replay-prev3**, source commit `8a85d4c9f080984a8c51d3abf3886bcb6c919853`.
Application SHA-256: `bd21a7ad830650ce1a4f45fca54d0e206888cb34fe72d7161aae26d0863d44f8`.

Street and Track now center each icon, fixed gap and measured label as one
unit. Native host captures were inspected and the full four-profile firmware
gate passed. The application region was reflashed and hash-verified; the
existing bootloader and partition table were retained. A 12-second boot capture
confirmed application version `8a85d4c`, PSRAM initialization and JD9365/LVGL
startup without a reported application error.

Evidence: [application flash](bench/2026-11-19/flash-icons.log) and
[boot output](bench/2026-11-19/boot-icons.log). The earlier upright/animated user
confirmation below applies to initial bring-up; this alignment correction was
visually verified in native host captures.

## Initial bring-up — 2026-11-19

The local M1 Pro Mac identified the board through **USB-PROG** as ESP32-P4
**revision 1.3**, with 32 MB flash. The replay boot detected and memory-tested
32 MB PSRAM and read LCD ID `93 65 04` from the JD9365.

Installed profile: **replay-prev3**, source commit
`ee4fd82446612b0fe127cbec81ed5215e531e983`.
Application SHA-256:
`ed2248403f4f258abe6e2cf4b9e201bd41069e34523485f17e88b7b478eeb5b1`.

The bootloader, partition table and application were flashed through
`/dev/cu.usbmodem1101`; esptool verified every written region. The application
booted with ESP-IDF 5.5.5, initialized MIPI DSI/JD9365, started LVGL and enabled
PPA rotation. No application error or restart was reported during the 18-second
boot capture. The user subsequently confirmed an **animated dashboard, upright**. This
verifies basic visual orientation and animation, not measured frame rate,
driving readability or longer-term stability.

Evidence: [flash verification](bench/2026-11-19/flash.log) and
[boot output](bench/2026-11-19/boot.log). Device MAC is omitted from the saved
flash log. Before writing, the affected flash prefix was backed up locally
(0x00000000–0x0010ffff, not the full 32 MB device).

## Remaining physical checks

- Brightness and physical mode-control operation.
- Startup-to-visible-image timing, frame pacing and sustained operation.
- ECU UART translation, wiring, configuration and concurrent USB tuning.
- External sender calibration and SD behavior in the intended power system.

This installed image is replay-only: it does not communicate with the ECU.
The current [firmware guide](../../firmware/cluster/README.md) describes the
build profiles and the separate live commissioning procedure.
