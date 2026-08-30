# Pi key-state input and TSDash logging

## Architecture

The existing UPS monitor remains the state authority. Every 0.5 seconds it reads
INA219 current using the established `-0.20 A` boundary:

- `connected` publishes HIGH to a one-line `gpio-mockup` software input.
- `discharging` publishes LOW.
- Invalid I2C samples retain the last published state.
- Sustained discharge still invokes the existing 240-second OS poweroff path.

The Pi4J bridge maps only TSDash logical GPIO17 to that software GPIO. Physical
RP1 GPIO17 and the UPS/J2 wake circuit are untouched. TSDash provisions the input
active-high with pull resistance `OFF` and exposes `AppEvent.ignitionOn`.

The software GPIO defaults HIGH during boot so TSDash cannot pre-qualify a false
key-off before Python's first valid sample. A valid discharge sample overrides it
LOW even while the Pi continues running from the UPS.

## Logging

TSDash is reconfigured at every launch in Expression mode:

- Start: `rpm > 0 && AppEvent.ignitionOn != 0`
- Stop: `AppEvent.dataLogTime > 5 && isTrueFor(AppEvent.ignitionOn == 0, 2)`

The start and age guards prevent immediate stop/restart races. TSDash performs its
native stop action; it is not restarted on key-off.

## Verified 2026-08-30

- Python transition unit tests pass on macOS and the Pi.
- High-level Pi4J reads and live LOW/HIGH callbacks pass.
- Physical RP1 GPIO17 remains untouched.
- A clean-session test log stayed open after start and closed on software key-off.
- A 223-row `.mlg` converted successfully and matched its USB copy by SHA-256.
- Physical power loss drove the software input LOW and the Pi shut down after the
  existing four-minute delay.

Remaining acceptance: one solid physical crank followed by key-off, conversion of
that same `.mlg`, and comparison of its source and USB hashes.
