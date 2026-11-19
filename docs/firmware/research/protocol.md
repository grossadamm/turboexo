# TurboExo Speeduino Serial3 telemetry

The Mega2560 sends the requested span of the 130-byte TunerStudio output
channel map over Serial3 at 115200 8N1. The dash can cover all selected
channels with two reads per cycle, of offsets 0–43 and 76–108. Each reply
starts with `72 30` and fits in an empty AVR UART transmit buffer. USB
TunerStudio uses a separate handler in **Generic (ini File)** mode. The firmware sources and
saved tune establish the protocol. The installed board, active configuration,
electrical interface and concurrent USB performance still need bench verification.

## Firmware identity and configuration

| Supported source tag | Source commit | Exact secondary `S` reply |
|---|---|---|
| `202501` | `29bdaa32fc35764094e281f169754714100ce1f0` | `Speeduino 2025.01` |
| `202501.6` | `6429cdd1bc72eb63cbb7668b06f34f064cbfc929` | `Speeduino 2025.01.6` |
| `202501.7` | `cd3d0e38d276a7bd087a9dc86fd976780539ce8f` | `Speeduino 2025.01.7` |

The saved repo and TunerStudio project MSQs both identify `Speeduino+2025.01.6`.
Their `speeduino 202501` signature identifies the INI family. Source diffs of
these three tags confirm the same query routing for Generic, reply framing and
output map. The distinct TunerStudio mode changes serial routing and is outside
this profile. [Base S/Q behavior](https://github.com/speeduino/speeduino/blob/29bdaa32fc35764094e281f169754714100ce1f0/speeduino/comms_legacy.cpp#L645-L679)
· [.6 S/Q behavior](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/comms_legacy.cpp#L645-L679)
· [.7 S/Q behavior](https://github.com/speeduino/speeduino/blob/cd3d0e38d276a7bd087a9dc86fd976780539ce8f/speeduino/comms_legacy.cpp#L645-L679)
· [Secondary mode dispatch](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/comms_secondary.cpp#L38-L59).

Use an explicit Serial3 Generic profile and confirm identity at runtime with
one raw byte `53` (ASCII `S`). Wait for a bounded quiet interval before matching
the complete, case-sensitive ASCII reply. A base-version prefix can also occur
at the start of a patch-version reply. The supported replies are 17 or 19 bytes
without a terminator, length byte or checksum. ASCII `Q` (hex `51`) is a read-only
diagnostic and returns `speeduino 202501` on all three, so it cannot distinguish
them. Identity alone cannot identify the configured comms mode. A settings
check in TunerStudio and a validated telemetry reply are required. If identity
is unsupported, keep the interface disconnected from telemetry.

The current disk tune shows secondary serial **Disable** and **Generic (Fixed
List)**. An operator must verify the active ECU configuration and perform any
required setup in TunerStudio. Initialization calls `Serial3.begin(115200)`
only when the setting is enabled, so confirm the port after an ECU restart.
The dash sends only its fixed identity and telemetry commands. The secondary
dispatcher also recognizes tuning commands, so the dash UART must be dedicated
to this client and isolated from terminal, boot-log and debug output. [AVR
port selection](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/board_avr2560.cpp#L20-L29)
· [Initialization](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/init.cpp#L169-L199)
· [Secondary command dispatch](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/comms_secondary.cpp#L52-L155)
· [CurrentTune](../../../CurrentTune.msq#L1487).

Enabling the interface changes which page-9 bits select local Aux inputs.
The saved tune specifies `caninput_sel0a=Analog_local` for disabled secondary
serial and `caninput_sel0b=Digital_local` for enabled secondary serial. A
configuration check must verify that Aux0 remains analog A8 in the enabled
mode before using the Spartan status channel and review the other Aux selections.
Oil pressure uses the dedicated A9 input. Keep the link point-to-point and check
whether external Aux sources send unsolicited Serial3 traffic. [INI
selectors](../../../projectCfg/mainController.ini#L833)
· [Aux polling branches](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/speeduino.ino#L319-L375)
· [Project wiring](../../WIRING.md).

## Transaction and timing

| Part | Bytes |
|---|---|
| Request | ASCII `r`, CAN ID `00`, subcommand `30`, start offset U16LE, data count U16LE |
| First read, offsets 0–43 | `72 00 30 00 00 2C 00` |
| Second read, offsets 76–108 | `72 00 30 4C 00 21 00` |
| Response | ASCII `r`, `30`, requested data bytes in order |

CAN ID is consumed and ignored. The response carries only the two-byte echo
and payload, with no length, offset, transaction ID, CRC or error byte. The
legacy handler waits for all six bytes after `r`, accepts only subcommand
`30`, and passes offset/count to the sender without bounds checks. Unrecognized
subcommands give no reply. The sender uses an 8-bit loop index, so only send the
fixed reads. Enforce at most 48 data bytes per read. `A` sends 75 data bytes
and `n` sends 123, with different headers and mode-dependent mapping. Fixed and RealDash modes also emit the same
`r` echo and map. Confirm Generic (ini File) independently. [Legacy
parser and sender](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/comms_legacy.cpp#L645-L761)
· [INI command and map size](../../../projectCfg/mainController.ini#L5331).

Send the complete request in one UART write after confirming transmit capacity.
The two requests expect fixed 46- and 35-byte replies. Index a chunk with
`wireIndex = 2 + fieldOffset - requestedOffset`. Use one transaction at a time
and accept only an exact-length, correctly prefixed response before its deadline.
Use a short idle guard to detect excess bytes before publication. Keep the
chunk timestamps and publish a combined snapshot only after both reads in the
same cycle. Treat `72 30` found in a payload as ordinary
data. After a malformed or incomplete response, discard the entire transaction,
drain incoming bytes to a quiet interval and back off before a new identity and
read. If the request itself may have been truncated, stop transmitting and
restart the ECU under controlled bench conditions. The legacy handler can wait
indefinitely for the rest of a partial request and can consume a resend as its
arguments. Treat transport freshness independently of engine and sensor validity.
Without a CRC, even an exact-length frame can contain corrupted data.

### Recovery after uncertain transmission

For a known idle Generic parser receiving only an exact whole-byte prefix of
one whitelisted command, completing the prefix with NUL bytes would leave the
parser idle. NUL has no standalone command case. A partial `r` prefix that
ends before the subcommand would complete with an unsupported subcommand and
give no reply. A prefix that includes the subcommand would yield a zero-length
read unless the original low count byte had already arrived, in which case it
would yield the original bounded read. A complete `S` or `r` would run as
usual. A completed read can drain surplus NULs from its own RX buffer.

An independent dash brownout can cut transmission inside a UART character.
If the line returns to idle high partway through an intended zero byte, the
receiver can sample changed data bits with a valid stop bit. A corrupted
length byte can make the selected legacy sender stall before another
command can be parsed. The exact-prefix proof therefore cannot establish safe
recovery from a brownout. Start every live dash boot with TX inhibited.
After an uncertain request, return to the same inhibited state. Resume
only after the operator confirms an actual ECU reset. A complete transmit
followed by a malformed receive can use the normal drain and re-identify path.
[Secondary command switch](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/comms_secondary.cpp#L52-L155)
· [Legacy receive and transmit loops](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/comms_legacy.cpp#L649-L761)
· [ATmega2560 datasheet, USART frame format and receiver errors](https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/ATmega640-1280-1281-2560-2561-Datasheet-DS40002211A.pdf).

The AVR loop checks USB and the secondary port separately. Legacy Serial3
transmission waits when its UART buffer fills and discards pending RX after
sending. This is why the client must avoid pipelining. Each selected reply fits
the approximately 64-byte transmit buffer if it is empty. The 46- and 35-byte
replies take about 4.0 and 3.0 ms on the wire at 115200 8N1. A single 111-byte
reply would spend about 9.64 ms on the wire and could wait about 4 ms in the
main loop as it enqueues its tail. Set the initial cap at 5 complete cycles per
second and test USB live gauges, logging, ECU loops per second and sync-loss
counters at key-on and stationary idle. Reading live
channels updates the sync bit, refreshes the free-RAM status when requested, and
clears the transient VSS refresh flag. The requests write no calibration pages.
[ECU loop scheduling](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/speeduino.ino#L100-L128)
· [Sender](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/comms_legacy.cpp#L694-L763)
· [AVR buffer assumption in firmware](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/globals.h#L392).

## Telemetry decoder

Offsets are zero-based in the complete ECU channel map. U16 is
little-endian. Decode S8 as two’s complement, convert unsigned temperatures to
a wider signed type before subtracting 40, and store engineering units
consistently across C++ and UI.

| Channel | Payload offset | Wire type | Decoding |
|---|---:|---|---|
| ECU seconds | 0 | U8 | Seconds counter, modulo 256 |
| Engine status | 2 | U8 | Bit 0 running, bit 1 cranking, bit 2 ASE, bit 3 warmup enrichment |
| Sync loss counter | 3 | U8 | Raw counter |
| MAP | 4–5 | U16 | kPa absolute |
| IAT | 6 | U8 | raw − 40 °C |
| CLT | 7 | U8 | raw − 40 °C |
| Battery | 9 | U8 | raw × 0.1 V |
| Measured AFR | 10 | U8 | raw × 0.1 AFR |
| RPM | 14–15 | U16 | RPM |
| Reported AFR target | 21 | U8 | raw × 0.1 AFR, subject to startup echo |
| Ignition advance | 24 | S8 | Degrees |
| TPS | 25 | U8 | raw × 0.5% |
| Loops per second | 26–27 | U16 | ECU loop performance |
| Boost target | 30 | U8 | raw × 2 kPa absolute |
| Boost duty | 31 | U8 | ECU output duty % |
| Status2 | 32 | U8 | Bit 7 full sync |
| Baro | 41 | U8 | kPa absolute |
| Aux0 | 42–43 | U16 | Raw input counts if configured as analog local A8 |
| Injector PW1 through PW4 | 76–83 | Four U16 | Raw µs each, multiply by 0.001 for ms |
| Status3 | 84 | U8 | Bit 4 half sync, bits 5–7 squirts per cycle |
| Engine protection | 85 | U8 | Bits 0–4 RPM/MAP/oil/AFR/coolant protection, bit 7 I/O error |
| ECU speed | 104–105 | U16 | km/h when VSS is configured |
| ECU gear | 106 | U8 | 0 unknown |
| ECU fuel pressure | 107 | U8 | psi if configured |
| ECU oil pressure | 108 | U8 | psi if configured |

For TurboExo’s four-stroke engine, calculated PW1 injector duty is
`PW1_us × rpm × nSquirts / 1_200_000` percent. Use floating point or
sufficiently wide arithmetic. Require the live squirt count to be nonzero.
An RPM of zero yields zero calculated duty. A reading above 100% is
diagnostic evidence rather than a scale to clamp. PW is the commanded pulse,
and sequencing can cause a channel's reported PW to be zero while a paired
physical output fires. Keep boost duty separate from calculated injector duty.
Relative boost is `(MAP_kPa − baro_kPa) / 6.894757` psi when both inputs are
valid. Preserve the sign for vacuum. [Logger map](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/logger.cpp#L19-L177)
· [Squirt count packing](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/init.cpp#L868)
· [INI scales and calculations](../../../projectCfg/mainController.ini#L5337).

## Field validity

- The saved tune has Include AFR off, wideband selected and a 15 s EGO delay.
  While ECU `runSecs <= ego_sdelay`, the AFR target field mirrors the O2 channel.
  `runSecs` resets at stop or crank and is absent from the wire map. Byte 0
  `secl` counts ECU uptime, can wrap, and is not this timer. Start a conservative
  host timer on observed running with sync, reset it on crank, stop, loss of
  freshness or restart, and wait beyond the configured delay. AFR/target equality
  alone cannot determine whether the target is live. If Include AFR is turned
  on, target lookup happens immediately. [AFR target
  logic](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/corrections.cpp#L600-L615)
  · [Running and crank logic](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/speeduino.ino#L425-L459)
  · [Timers](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/timers.cpp#L254-L277).
- AFR is a filtered ADC conversion with no heater-ready bit in the response.
  Short-start Spartan voltages have mapped to apparent 13.1–13.2 AFR. Keep
  measured AFR unavailable until readiness is established. Aux0 can qualify
  readiness after the installed controller mode and raw ADC levels are confirmed.
  Historic raw counts differ from nominal voltages, so the available evidence
  cannot justify a fixed threshold. [O2 sensor read](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/sensors.cpp#L675-L690)
  · [Spartan wiring and observations](../../WIRING.md#wideband-replacement).
- Saved VSS is Off, so zero from the ECU does not establish vehicle speed.
  Keep speed unavailable until there is a configured and validated speed source.
  Oil pressure returns zero when disabled and clamps readings to its configured
  range. There is no dedicated transducer-fault indication in the packet.
  Native oil pressure is distinct from the separate ADS1115 oil-temperature
  sender, and ECU fuel pressure is distinct from the ADS1115 fuel-level sender.
  Show those fields with their own source and validity. [VSS
  logic](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/sensors.cpp#L754-L795)
  · [Pressure conversions](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/sensors.cpp#L822-L852).
- The ECU updates VSS at 10 Hz and CLT, IAT, battery and oil pressure at 4 Hz.
  Repeated numeric values can be fresh samples. Use local monotonic receive
  times to age the link. Full or half sync and the running/cranking bits cover
  engine state, while warmup enrichment indicates only ECU fuel correction.
  The status flags do not qualify all sensor channels as valid. [ECU sensor
  cadence](https://github.com/speeduino/speeduino/blob/6429cdd1bc72eb63cbb7668b06f34f064cbfc929/speeduino/speeduino.ino#L275-L317).

## UA4C connector

The manufacturer’s vC5 White Fang schematic, sheet 1, shows **P4 SER3**.
The schematic copy archived on local main matches the manufacturer's file
by SHA-256 `2c5774f148fc0ca9cada3936aae0cad9f5bca53fcf500b32d216bd0b9c201f20`.

| UA4C vC5 P4 pin | Signal | Connection |
|---|---|---|
| 1 | ECU TX3, Mega D14 | Level translator toward dash UART RX |
| 2 | ECU RX3, Mega D15 | Level translator from dash UART TX |
| 3 | ECU ground | Signal reference |
| 4 | ECU +5 V rail | Leave unconnected for separately powered dash |

The direct Mega UART is 5 V logic. Use a translator for both directions
matched to the actual ESP32-P4 board GPIO voltage domain, with behavior
verified for independent on/off sequences. P3 SER0 routes the separate
Bluetooth/USB UART nets. Jumpers JP10/JP11 can share the Serial3 lines
with GPO/GPI when bridged. Verify the installed revision, P4 orientation,
jumper positions, signal levels, and no second driver before connecting.
The target ESP32-P4 board connector and GPIO selection require its own
schematic. [WTMtronics UA4C vC5 schematic](https://github.com/turboedge/SpeedyBoards/blob/99f347851e743aa804df6a228b2b2adc38b9c06f/UA4C/vC5-WHITE%20FANG/SCHEM/UA4C-vC5.pdf)
· [Arduino Mega pinout](https://docs.arduino.cc/resources/pinouts/A000067-full-pinout.pdf)
· [Espressif ESP32-P4 electrical characteristics](https://www.espressif.com/sites/default/files/documentation/esp32-p4_datasheet_en.pdf).

## Decoder and bench test vectors

Make a synthetic 109-byte channel map and zero all unused fields.
Set the following values, then split offsets 0–43 and 76–108 into separate
frames prefixed with `72 30`. Verify the expected results.

| Payload offsets | Hex bytes | Expected |
|---|---|---|
| 0, 2, 3 | `FE`, `01`, `03` | Uptime 254 s, run true/crank false, 3 sync losses |
| 4–5, 6, 7 | `2C 01`, `23`, `76` | MAP 300 kPa, IAT −5 °C, CLT 78 °C |
| 9, 10, 21 | `8A`, `83`, `8E` | 13.8 V, AFR 13.1, reported target 14.2 |
| 14–15, 24, 25 | `34 12`, `F9`, `4B` | 4660 RPM, −7°, 37.5% TPS |
| 32, 41, 42–43 | `80`, `63`, `56 02` | Full sync, 99 kPa baro, Aux0 598 counts |
| 76–77, 84 | `E8 03`, `40` | PW1 1.000 ms, 2 squirts, duty 7.7667% |
| 104–105, 108 | `2D 01`, `37` | 301 km/h raw decoded speed, 55 psi oil |

Feed that response one byte at a time and in varying chunk sizes. Embed
`72 30` at an unused payload location. Test short, long, wrong-header and
delayed replies, UART errors, startup bytes, timeout, disconnect and recovery.
For identity, split the suffix from its prefix and reject unsupported suffixes
and extra bytes. For validity, test initial key-on, crank, consecutive
cranks, stable running beyond delay, sync loss, stopped engine and `secl`
wrap. Verify disabled VSS, unknown oil configuration and unknown Spartan
readiness remain unavailable despite transport freshness.

Before powering the dash/ECU link, confirm revision and signal levels and
verify the exact transmitted bytes against a UART fixture. After an operator
configures the bench ECU, compare captured Serial3 channel values against live
TunerStudio with USB connected. Check a key-on cycle and later a stationary
idle run with the dash enabled and disabled at the initial rate. Record ECU
identity, firmware mode, packet bytes, link latency/timeouts, USB logging
behavior, loop rate and sync-loss counters before increasing the poll rate.
