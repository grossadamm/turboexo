# Current wiring and I/O assignments

Updated 2026-10-17. This is the current signal-assignment reference; old commissioning
notes describe earlier hardware. It is not a complete connector-cavity or wire-color
pinout. Assignments below distinguish documented wiring from staged ECU settings.

## Ignition and injection

| UA4C output | Connection | Evidence |
|---|---|---|
| IGN1 | Cylinder 1 COP | Physical wiring corrected; user confirmed running 2026-10-10 |
| IGN2 | Cylinder 3 COP | Same |
| IGN3 | Cylinder 4 COP | Same |
| IGN4 | Cylinder 2 COP | Same |
| INJ1 | Cylinder 1 injector | Rewired and individually hardware-tested; user confirmed 2026-10-17 |
| INJ2 | Cylinder 3 injector | Same |
| INJ3 | Cylinder 4 injector | Same |
| INJ4 | Cylinder 2 injector | Same |

Cylinder 1 is at the timing-belt end; firing order is 1-3-4-2.
**2026-10-10 confirmation:** correcting the COP connections to the map above
restored running. The prior physical order is unknown; the earlier recorded map
was not proof of actual harness connections. In Wasted COP, IGN1+IGN3 fire
cylinders 1+4, and IGN2+IGN4 fire cylinders 3+2.

**2026-10-17 confirmation:** user individually tested both injector and coil
outputs and confirmed the same 1 -> 1, 2 -> 3, 3 -> 4, 4 -> 2 map for both.
This supersedes the September injector map. The Semi-Sequential pairing selector
names ECU outputs: select **1+3 & 2+4**, giving physical cylinders 1+4 / 3+2.
Wasted COP uses those same output pairs automatically. Output testing verifies
connections/operation, not actual crank-relative spark timing.

Four Toyota/Denso 673-1300 / 90919-02239 COPs replace the original Miata coil packs
and plug leads. Current saved ignition mode is **Wasted COP**; earlier Sequential
mode is historical. Do not substitute stock-coil dwell specifications.

Current injectors are stock 238 cc red Denso units. Saved injection mode is
**Semi-Sequential**, output pairing 1+3 / 2+4 (physical cylinders 1+4 / 3+2).
The individual injector wiring is important:
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

After the October 17 reset, the disk tune briefly assigned native oil pressure to
A8 and Aux0 to A9. The 13:41 repair restores native oil monitoring to A9 with
-13/113 psi endpoints, and Aux0 analog status to A8. The explicit load file is
`TurboExo_oilpressure_fixed_2026-10-17_134104.msq`; burn, full power-cycle and
readback remain pending. The repair does not independently verify sensor wiring
or actual pressure.

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

### Expected Spartan status connection and readings

- Brown status output → UA4C INP1 → MCU A8 → Aux0, configured Analog_local.
  The Spartan v2 default output mode is heater status (`GETNBMODE` should report
  mode 2); actual installed revision and mode have not been read back.
- Spartan black electronics ground should share the interfacing ECU's ground
  reference, per the Spartan manual. White heater ground goes to chassis/engine
  ground. Existing physical grounding has not been verified here.
- With a nominal 5 V ADC reference, the expected raw 10-bit readings are:

| Heater state | Brown-wire voltage | Nominal Aux0 raw value |
|---|---|---|
| Waiting for trigger | 0 V | 0 |
| Heating started | 1 V | about 205 |
| Heat-up complete; heater closed loop | 2 V | about 409 |

Raw ADC counts are dimensionless readings, not volts. Nominal conversion is
`V = counts * 5 / 1023`; reference voltage, grounding and input loading affect
comparison with the actual wire voltage. These are expected values, not newly
validated thresholds. Readiness does not establish AFR calibration accuracy.

### UA4C input conditioning and expected jumper configuration

The UA4C **vC5 White Fang schematic**, page 5, shows:

| Input | Bias selection | Bias resistor | Series filter resistor |
|---|---|---|---|
| INP1/A8 (Spartan status) | JP7: +5 V or ground | R6, 2.49 kΩ | R9, 470 Ω |
| INP2/A9 (oil pressure) | JP8: +5 V or ground | R7, 2.49 kΩ | R8, 470 Ω |

Both also have filter capacitors and protection diodes. There is no amplifier
or intentional 2 V→3 V conversion. **For these externally driven voltage outputs,
the expected commissioning configuration is no external bias: leave JP7/JP8
unbridged so neither pull-up nor pull-down loads the signal.** This is a circuit-
based recommendation, not a documented factory-default claim. Confirm the actual
board revision and physical jumper state before changing hardware; neither has
been established from these logs. No jumper change has been performed.

An enabled pull-up could raise the measured signal depending on source drive;
it has not been proven to explain Aux0 around 598 (nominal 2.92 V). Compare the
brown-wire voltage relative to Spartan electronics ground and ECU ground with
simultaneous Aux0, and inspect JP7. Similarly, verify JP8 when investigating oil
pressure. Do not compensate by inventing a new status threshold or oil scale.

Sources: [UA4C connection sheet](https://github.com/turboedge/SpeedyBoards/blob/master/UA4C/DOC/Connections.pdf),
[vC5 schematic](https://github.com/turboedge/SpeedyBoards/blob/master/UA4C/vC5-WHITE%20FANG/SCHEM/UA4C-vC5.pdf),
local `tmp/pdfs/UA4C-vC5.pdf`, and Spartan v2 manual pages 1 and 3 in
[manuals](manuals/README.md). The general Speeduino **v0.4 board is different**:
its A8 primary-O2 mapping and jumper guidance must not replace the UA4C map.
On the UA4C, primary O2 is MCU A1; its physical harness connection remains unverified.

## IACV and charging

IACV electrical connection is unchanged. Current saved settings are one PWM channel,
500 Hz, Normal direction, PWM Closed+Open loop. Physical valve response and the
new controller setup remain unverified; see STATUS.md. Do not invent a harness
cavity assignment from a software default.

Alternator charging is confirmed by the September 28 logs rising from 12.1 V before
cranking to 13.8–14.7 V while running, with the user confirming no charger or donor
vehicle attached. This confirms charging operation, not individual alternator-wire
routing or maximum-current capability.

## Power/backfeed incident — 2026-10-11

User identified a light backfeeding voltage, disconnected it, and confirmed the
Bluetooth problem was fixed. Before disconnection, the Bluetooth LED was dark
and the Pi could not connect, even though USB ECU communication worked and ECU
battery telemetry reached 12.0 V with the key on. The light's identity, wiring,
backfeed path and voltage were not supplied; no permanent circuit modification
has been specified or verified. Preserve this as a known diagnostic lead.

A responding USB interface and normal ECU battery telemetry do not verify the
Bluetooth module's supply. Check actual power and backfeed paths before blaming
pairing, firmware or tune loss. Disconnect USB as well as vehicle power when
checking complete shutdown; account for accessory feeds. Full evidence and its
limits are in EXPERIMENT_LOG.md, October 11.


## Boost hardware identified by seller listings — 2026-10-18

BOV: generic25mm atmospheric VW/Audi1.8T/Bosch-replacement style, advertised25psi.
Solenoid listing:35A-AAA-DDBA-1BA,12V5.4W3-port. See REFERENCE.md and saved
screenshots in docs/hardware. These are seller specifications, not authenticated
part testing. Actual port routing and connection to saved boostPin12 remain
unverified. BOV small reference hose should sense post-throttle manifold pressure;
physical hose routing has not been independently inspected. Prepared tune disables
boost output pending pressure/flow tests;0% command does not prove wastegate position.
