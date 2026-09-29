# Current wiring and I/O assignments

Updated 2026-09-28. This is the current signal-assignment reference; old commissioning
notes describe earlier hardware. It is not a complete connector-cavity or wire-color
pinout. Assignments below distinguish documented wiring from staged ECU settings.

## Ignition and injection

| UA4C output | Connection | Evidence |
|---|---|---|
| IGN1 | Cylinder 1 COP | User wiring recorded 2026-09-25 |
| IGN2 | Cylinder 3 COP | Same |
| IGN3 | Cylinder 4 COP | Same |
| IGN4 | Cylinder 2 COP | Same |
| INJ1 | Cylinder 1 injector | Individual harness wiring recorded 2026-09-25 |
| INJ2 | Cylinder 2 injector | Same |
| INJ3 | Cylinder 3 injector | Same |
| INJ4 | Cylinder 4 injector | Same |

Cylinder 1 is at the timing-belt end; firing order is 1-3-4-2.
Four Toyota/Denso 673-1300 / 90919-02239 COPs replace the original Miata coil packs
and plug leads. Current saved ignition mode is **Wasted COP**; earlier Sequential
mode is historical. Do not substitute stock-coil dwell specifications.

Current injectors are stock 238 cc red Denso units. Saved injection mode is
**Semi-Sequential**, pairing 1+4 / 2+3. The individual injector wiring is important:
the earlier Paired setting drove only INJ1/INJ2 in this firmware. Logged PW3/PW4=0
in Semi-Sequential does not mean physical INJ3/INJ4 are inactive. See September 25
experiment entry and its firmware evidence.

## Spare analog inputs

| Connector signal | MCU pin | Assignment | State |
|---|---|---|---|
| INP1 | A8 | Spartan second/status output, Aux0 / WideBandStatus | Existing documented connection and logged input |
| INP2 | A9 | Oil-pressure transducer signal | User-selected connection; native oil monitoring enabled in saved tune; physical completion/readings and ECU burn not yet confirmed |

INP1 and INP2 are both assigned; do not reuse either as a spare. Pin mapping is
from UA4C-vC5 schematic (`tmp/pdfs/UA4C-vC5.pdf`) and connection sheet. Aux0 is raw
counts, not a voltage display. Oil uses Speeduino's dedicated oil-pressure input,
not Aux1; Aux1 does not need enabling for oil-pressure monitoring.

## Oil-pressure sensor

User specification: 0.5 V = 0 psi, 2.5 V = 50 psi, 4.5 V = 100 psi.
Ideal pressure is `(V - 0.5) * 25`. Speeduino expects endpoints at 0/5 V;
exact extrapolation is -12.5/112.5 psi, saved as -13/113 because its fields store
whole psi. Oil-pressure protection stays **Off** pending verified pressure readings.
The user is handling supply, ground and connector wiring; those details have not
been documented here. Do not infer pin order or supply voltage from the output range.
See STATUS.md for the latest staged tune and burn/readback status.

## Wideband replacement

The user confirmed on 2026-09-28 that the old OEM module was replaced by a
**non-OEM Spartan with the separate status wire**. Use the manufacturer manuals
in [manuals/README.md](manuals/README.md), not the OEM module pinout.

The Spartan 3 v2 manual specifies green AFR output and brown heater-status output
(default mode): 0 V waiting, 1 V heating, 2 V heat-up complete. Exact replacement
hardware/firmware revision has not been read back. The existing status connection
is documented as INP1/A8. Warm Aux0 about 565–604 counts does not numerically match
2 V under a direct 5 V/10-bit assumption; verify the transfer or brown-wire voltage
before assigning readiness thresholds. Readiness does not verify AFR calibration.
The primary AFR signal's exact ECU connector cavity is not established in this note.

## IACV and charging

IACV electrical connection is unchanged. Current saved settings are one PWM channel,
500 Hz, Normal direction, PWM Closed+Open loop. Physical valve response and the
new controller setup remain unverified; see STATUS.md. Do not invent a harness
cavity assignment from a software default.

Alternator charging is confirmed by the September 28 logs rising from 12.1 V before
cranking to 13.8–14.7 V while running, with the user confirming no charger or donor
vehicle attached. This confirms charging operation, not individual alternator-wire
routing or maximum-current capability.
