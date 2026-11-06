# TurboExo Reference — pinned ground truth

Stable facts so agents don't re-derive or re-research them. Chronological history
lives in `EXPERIMENT_LOG.md`; current front line in `STATUS.md`.

> **Every claim here carries a provenance tag. Do not add a line without one.**
>
> - `[tune]` — read out of a `.msq` on disk. Re-checkable with `grep`.
> - `[log]` — measured in a datalog. Cite the log file.
> - `[user]` — the user physically observed/confirmed it. Cite the date.
> - `[src]` — read out of Speeduino firmware source.
> - `[web]` — from a cited external document.
> - `[inference]` — **deduced, not observed.** Never act on one without testing it first.
>
> Untagged assertions have repeatedly become confidently-wrong "facts" here. If you
> can't tag it, don't write it. If a `[tune]` line and the ECU disagree, the ECU wins —
> re-verify by back-solving PW from a log (see "Verifying the file matches the ECU").

## The rig

### Dashboard sensor board and wake components — saved 2026-10-30

**Build checkpoint, 2026-11-05:** [resume notes](hardware/ads1115/BUILD_STATUS.md).
H1 was installed socket-up with short solder tails. Its relocation is pending;
Rev H does not yet describe the repaired header position or mating pin map.
Do not follow its direct-stack instructions for the current physical assembly.


Start here before asking for these component identities or screenshots again.
Original user images are retained in [sensor-board-components](hardware/sensor-board-components/),
with [image provenance](hardware/sensor-board-components/image_provenance.json)
and [SHA-256 checksums](hardware/sensor-board-components/SHA256SUMS.txt).
Images establish the user's identified parts/listings, not the installed wiring
or measured electrical behavior. `[user + saved attachments: 2026-10-30]`

| Component | Established details | Remaining limits |
|---|---|---|
| ADS1115 breakout | User's blue 10-pin module; labeled VDD, GND, SCL, SDA, ADDR, ALRT, A0, A1, A2, A3, left to right in the supplied front view. [Saved image](hardware/sensor-board-components/ads1115_module_user_reference_2026-10-30.png). `[user/image: 2026-10-30]` | Exact vendor, chip identity, onboard capacitor values and pull-up connections/values have not been measured. Do not equate this generic module with a particular Adafruit revision. `[unverified: 2026-10-30]` |
| Oil-temperature sender | **Dweekiy**, Amazon **B07ZYWMV89**, advertised **1/8 NPT**, brass, one signal stud with return through the threaded body into the engine/sandwich plate. [Saved listing screenshot](hardware/sensor-board-components/dweekiy_oil_temperature_listing_user_2026-10-30.png), [exact listing](https://www.amazon.com/dp/B07ZYWMV89). `[user/image + web: 2026-10-30]` | No verified resistance-temperature curve, bias current or dissipation specification. This is distinct from the ECU oil-pressure transducer. `[web search result/limit: 2026-10-30]` |
| Fuel-level sender | Original **1999 Miata sender**, original gauge disconnected. User measured **110 ohms** and clarified that the tank was **very empty**. Preserve that as the actual reported observation. `[user: 2026-10-30; earlier observation recorded in EXPERIMENT_LOG.md]` | Do not replace the observed value with a published nominal point or treat a float inspection table as an exact liters curve. `[evidence limit: 2026-10-30]` |
| Brake-fluid reservoir switch | Original 1999 Miata type. Factory inspection: open above MIN, continuity below MIN. With an independent 3.3 V pull-up, normal reads HIGH and low fluid reads LOW. `[user + factory manual + circuit inference: 2026-10-30]` | Installed wiring must be independent of any powered warning-light circuit. An unplugged switch also reads open; this simple circuit cannot detect a broken wire. `[circuit inference: 2026-10-30]` |
| Optocoupler module | User-confirmed green module with INPUT +/− and VCC/OUT/GND terminals, red LED, R1, R2, and a four-pin optocoupler. [Saved front/back image](hardware/sensor-board-components/opto_module_front_back_user_2026-10-30.png). `[user/image: 2026-10-30]` | Earlier chats called it a PC817 module; the package marking is not sufficiently legible in this image to independently verify the exact part. R1/R2 values, input rating, CTR and actual installed connections remain unknown. `[image/evidence limit: 2026-10-30]` |
| UPS connection | The UPS is **not stacked as a HAT**; the user has connected it with jumpers. The new sensor carrier is intended to stack directly on the Pi with a **40-pin stacking header**, retaining accessible male pins above for existing UPS jumpers. `[user: 2026-10-30]` | Earlier assistant summaries identify a Waveshare UPS Module 3S V2; that exact revision is not independently confirmed from a current photo. Repository UPS code uses I2C bus 1, address 0x41. `[prior-chat attribution + scripts/pi/pi-ups-monitor.py: 2026-10-30]` |

**Optocoupler terminal orientation:** in the upper/front view of the saved image,
the left block is INPUT **+ above −**. The right block is **VCC above OUT above GND**.
The lower/back view is flipped; follow the printed labels, not the left/right
location from the front view. `[user image: 2026-10-30]`

**R1 lookup, 2026-10-30:** [DIYables' higher-resolution seller photo](https://diyables.io/images/products/pc817-1-channel-optocoupler-isolation-module-2.jpg)
of the matching PCB layout shows R1 as **brown-black-red-gold: 1 kohm +/-5%**.
Two independent image readings agree. [Local close-up](hardware/sensor-board-components/opto_matching_vendor_R1_closeup_2026-10-30.jpg)
and [matching front/back view](hardware/sensor-board-components/opto_matching_vendor_front_back_2026-10-30.jpg)
are saved with source URLs and checksums. This is an evidence-backed value for the
pictured seller variant, **not a measured value for the installed module**; do not
erase the distinction. The seller's unit is marked PC817C; that marking does not
independently identify the IC on the user's actual board. `[seller image + independent review: 2026-10-30]`

Using this R1 value with the proposed additional 470-ohm series resistor and
220 uF capacitor, a 12.6 V step with an assumed 3.2 V total LED drop gives about
6.39 mA initial input current and a 0.323 s current-decay time constant.
**The time constant is not the button-low duration.** Actual wake margin depends
on the optocoupler, J2 load/threshold and source/reset behavior. The proposed
10-kohm charger-input bleed draws 1.26 mA / 15.9 mW at 12.6 V. Exact assumptions
and additional bounds are in [nominal calculations](hardware/sensor-board-components/wake_nominal_calculations_2026-10-30.json).
No physical wake test or circuit change was performed by this lookup.
`[calculation, explicitly untested: 2026-10-30]`

**Wake calculation review, 2026-10-31:** reproducible step, source-ramp and
scenario calculations are in `scripts/analyze_wake_pulse.py` and
[the saved results](hardware/sensor-board-components/wake-analysis/calculations_2026-10-31.json).
The numerical ramp model was checked against the independent unshunted closed-form
solution. Scenarios explicitly assume source 12.0–13.2 V, total LED drop 2.7–3.7 V,
resistors +/-5% and capacitance +/-20%; these are not measured installed limits.
No published J2 threshold, input load or guaranteed minimum pulse was found.
The [firsthand ~200 ms Pi 5 J2 result](https://forums.raspberrypi.com/viewtopic.php?p=2326617)
is an empirical design reference, not a guaranteed specification. `[web + calculation: 2026-10-31]`

This review identified a separate **capacitor leakage/release issue**. The upstream
R7 bleed does not divert leakage around the optocoupler LEDs. As an example, the
[Nichicon UPW datasheet](https://www.nichicon.co.jp/products/pdfs/upw.pdf) allows up
to 0.03CV uA or 4 uA, whichever is greater, after one minute at rated voltage and
20 C: 165 uA for 220 uF / 25 V. This is an example specification, not identification
or a leakage measurement of the user's capacitor. Leakage could keep a sensitive
opto output active; this is a possible explanation for the reported faint LED,
not an established cause of the failed wake. `[datasheet + inference: 2026-10-31]`

**Included in Rev F after the user requested implementation:** a 4.7-kohm 1/4-W
resistor directly across the external optocoupler module's INPUT+ and INPUT-,
after R8, in parallel with D1. It is not across C6, and does not connect to the
module's OUT/GND/VCC terminals. At 165 uA, this holds the input around 0.776 V
(0.814 V with +5% resistance), diverting leakage around the series LEDs. Under
the nominal 12.6 V / 3.2 V LED-drop model, it reduces initial LED current from
6.39 to 5.78 mA and 200 ms current from 3.45 to 2.58 mA. Modeled LED conduction
ends around 0.69 s; this is not a guaranteed J2 low duration. It improves release
while reducing trigger drive, especially with a slowly rising source. Independent
review confirmed this tradeoff. Retain 220 uF rather than increasing capacitance
without evidence; a fixed-width pulse would require a different timing topology.
`[calculation + independent engineering review; implemented in layout, not physically tested: 2026-10-31]`

The rear traces appear consistent with **R2 between VCC and OUT**, i.e. an output
pull-up. This is a visual inference, not a continuity-tested schematic. It does
**not** establish that VCC must be connected to use the optocoupler as an external
pull-down: the target could provide its own pull-up. Conversely, the old instruction
to leave VCC disconnected is not a completed verification of this module and target
together. Do not choose a VCC voltage or decode uncertain resistor bands by guessing.
`[image/circuit inference; unverified topology: 2026-10-30]`

**Recorded failed wake attempt:** the chats “Trigger Pi boot from UPS power” and
“Find Raspberry Pi setup chats” describe a 220 uF series capacitor and reverse
diode across the module input, triggered by incoming charger power; OUT/GND went
to Pi 5 J2 and VCC was left disconnected. The earlier bare-PC817 suggestion used
an external 2.2 kohm resistor; the subsequent module advice omitted it, assuming
an onboard input resistor. The new photo confirms R1 exists but not its value.
User reported no automatic wake and an LED that flashed brightly, faded, then
glowed faintly again. LED activity did not prove the output voltage or pulse at J2.
No successful automatic-wake test or root cause has been established.
`[prior user/assistant chat record; new image: saved 2026-10-30]`

**Pi 5 wake connection:** [official documentation](https://www.raspberrypi.com/documentation/computers/raspberry-pi.html#power-button)
specifies a normally open momentary contact across the dedicated J2 pads.
J2 is not on the 40-pin GPIO header; Pi 5 uses its power button rather than GPIO3
for wake. Rev B's optional J5/J6 pair is only a passive extension requiring two
separate wires to J2; it does not implement the failed capacitor/optocoupler circuit.
Do not use the I2C SCL pin as the wake signal. `[web + layout: 2026-10-30]`

**Fuel factory inspection points:** [Mazda workshop scan, printed 09-22-7](https://www.mellens.net/mazda/Mazda-Miata-1999-2001.pdf#page=726)
gives FULL 6.4–7.6 ohms, 1/2 position 31.8–33.2 ohms, EMPTY 93–97 ohms.
With a nominal 3.300 V excitation and 1 kohm pull-up, the nominal 7/32.5/95 ohm
points produce 0.02294/0.10387/0.28630 V. The separately reported 110 ohms produces
0.32703 V. Factory inspection points and the user's very-empty observation are
different evidence; retain both. `[factory scan + calculation + user: 2026-10-30]`

**Oil research already performed:** exact ASIN/model/UPC searches, the Amazon
description and all product-gallery images, and alternative sender documentation
did not establish a Dweekiy calibration curve. Reseller identifiers are
**Dweekiycnuo426783**, UPC **738583183222** ([matching reseller](https://snapklik.com/en-ca/product/coolant-temperature-sensor-water-oil-temp-temperature-1-8-npt-electrical-sender-transmitter-sending-unit-temp-sensor/02CY4P879FDE5)).
The seller's 0–150 C / 0–300 F range is internally inconsistent; it is not a
calibration specification. The stud is signal; the body is return, not a second
insulated electrical terminal. `[web/image: 2026-10-30]`

For comparison only, [Z Car Depot 800-1035](https://zcardepot.com/collections/510/products/coolant-temperature-sender-universal-240z-260z-280z-510)
publishes 100/150/200/250/300 F at 450/158.2/64.3/29.25/14.96 ohms respectively.
**No verified electrical equivalence to Dweekiy was found. Do not load that curve
as this sender's calibration.** Measurements at known temperatures or an actual
manufacturer specification remain needed. `[web; explicitly unverified equivalence: 2026-10-30]`

**Current design artifact:** [Rev H DIYLC layout](hardware/ads1115/revH/ADS1115_sensor_board_revH.diy),
[machine-readable design and sensor evidence](hardware/ads1115/revH/layout_spec.json),
[soldering guide](../output/pdf/ADS1115_sensor_board_revH_soldering_guide.pdf).
Rev H adds only J8, a 2-pin optocoupler input header at (19,13) INPUT+
and (20,13) INPUT-, plus W33 from D1 K and W34 from R7 lower return pad
(23,9) via (23,13). Every existing Rev G component, bus and wire route is
unchanged so the in-progress soldered assembly can be retained. J7 takes the
switched regulated charger trigger; J6 takes optocoupler OUT/GND; J5 connects
to the Pi dedicated power-button header. VCC on the optocoupler stays unused.
`[user-requested additive header update: 2026-11-01]`

Rev G removes the unused F1/F2/C1/C2 filter positions and LK1/LK2 bypass
links at the user's request. Direct insulated W12/W18 connections replace those
paths; unused filter ground taps are removed. All other components and electrical
connections remain as in Rev F. R3 oil bias remains empty and J3 unplugged.
`[layout update: 2026-11-01]`
Review correction: W18 now routes via (18,12) and (10,12), avoiding J6/R8
terminals. The PDF depicts the full 6.3 x 2.5 mm R9 body and notes its tight
lead bends and actual connector/socket dry-fit requirements. Electrical endpoints
and component values are unchanged. `[review correction: 2026-11-01]`

Rev F retains every Rev E feature and adds **R9=4.7 kohms, >=1/4 W** at (15,5)-(15,8)
across the external optocoupler INPUT+/INPUT- nets on the carrier, in parallel with
D1 after R8. W31/W32 connect it; W24/W29 were locally rerouted for clearance.
Its maximum drawn body is 6.3 x 2.5 mm on 7.62 mm lead spacing; dry fit remains
unverified. The native file, wiring table, schematic and BOM include R9. Independent
review confirmed the restored circuit remains intact and the shunt reaches the
correct input nets, not C6 or the Pi output terminals. `[layout + review: 2026-10-31]`

The user clarified on October 31 that the request was **layout cleanup, not feature
removal**. Rev E restores the complete Rev C electrical design and cleans up visual
grouping, labels and wire rendering. Its component, wire and bus specifications
were checked for exact equality with Rev C. It retains the 24 x 18 individual-pad
board, direct 40-pin stacking connection, two straight buses, R1=1 kohm fuel bias
and R5=10 kohm brake pull-up; R3 oil bias and optional filters remain empty,
LK1/LK2 fitted. Physical pins 1=3V3, 3=SDA, 5=SCL, 9=GND, 13=GPIO27 brake
(proposed, live availability unverified). Pins 2/4 pass through without connecting
to the sensor circuit. `[user correction + independent artifact review: 2026-10-31]`

**Rev D is superseded.** Its omitted wake circuitry was the assistant's mistaken
interpretation of the cleanup request. Do not use Rev D's empty-wake instruction
as the current design. Rev E includes J5/J6/J7/R7/R8/C6/D1 and W23-W30; the prior
oil-bias and optional-filter decisions are unchanged. `[user + artifact checks: 2026-10-31]`

Rev E includes the same **proposed, untested wake input network** as
[Rev C](hardware/ads1115/revC/ADS1115_sensor_board_revC.diy):
J7 receives a switched, regulated nominal 12.6 V charger trigger; C6 is 220 uF
(>=25 V, maximum 8 mm body), positive toward J7+; R8 is 470 ohms (>=0.5 W)
between C6 negative and the external module's INPUT+; R7 is 10 kohms (1/4 W)
across J7 before C6; D1 is 1N4148, cathode/band to INPUT+, anode to INPUT-.
The existing optocoupler remains **external**. Module OUT/GND connect through
J6/J5 to the Pi's dedicated J2 pads; module VCC remains unconnected. Neither
charger wire is intentionally tied to the carrier's Pi rails. Replace the old
capacitor/diode pulse network rather than cascading two networks. Independent
native netlist review verified C6 polarity, D1 band placement and separate net
groups; no physical fit or wake test was performed. `[layout + independent review: 2026-10-30]`

The wake circuit does not detect whether the Pi is already running: a charger
return edge also presses its power button in that state. Running-state handling
and actual low/release timing remain to be verified before unattended use. The
guide includes a temporary pull-up for testing the disconnected open-collector
output; remove that test pull-up before connecting J2. `[circuit behavior and proposed test: 2026-10-30]`

The layout has no validated automotive overvoltage/transient protection. Physical
fit, module electrical values and GPIO availability remain unverified; native
netlist checks are not physical tests. Pi numeric sensor ingestion into TSDash is
still unproven: the existing key-state bridge is digital. Available public
TSDash 0.9.09.02 code did not expose a supported numeric publishing path; the
documented installed 0.9.09.10 build could not be inspected while the Pi was
unreachable. `[design/test limits + code inspection: 2026-10-30]`

### Bypass valve and boost solenoid — identified listings, 2026-10-18
- User-supplied [BOV listing](hardware/bov_25mm_seller_listing_2026-10-18.jpg): generic aluminum atmospheric25mm-OD valve, VW/Audi1.8T plastic-Bosch-diverter replacement style, advertised operational up to25psi; no exact brand/model or authenticated pressure rating.25psi is an operating claim, not an opening threshold. `[user-supplied seller screenshot, 2026-10-18]`
- User-supplied [solenoid listing](hardware/boost_solenoid_seller_listing_2026-10-18.jpg):35A-AAA-DDBA-1BA,3-port,12V,5.4W,25.4ohm, advertised vacuum–120psi. Genuine MAC provenance and actual markings/port plumbing not yet checked. `[user-supplied seller screenshot, 2026-10-18]`
- [MAC35 catalog](https://macvalves.com/wp-content/uploads/PDFs/Series_Pages/Sm3ways/35catalog.pdf) describes35A-AAA universal3-way,1/8NPTF, with multiple plumbing arrangements. Verify deenergized/energized flow before assigning pressure/actuator/vent lines;120psi rating of the solenoid does not rate the BOV/fixture. `[web: MAC catalog, checked2026-10-18]`
- BOV reference must sense post-throttle manifold conditions; test charge-side pressure versus reference pressure, not a universal opening PSI. Wastegate actuator pressure test is distinct. [Garrett valve roles](https://www.garrettmotion.com/knowledge-center-category/racing-and-performance/what-is-the-difference-between-a-wastegate-and-a-blow-off-valve/). `[web]`
- Proposed BOV bench fixture: short25mm-ID reinforced pressure-rated boost coupler, matching25mm-OD purpose-made metal air-feed adapter, positively retained/beaded hose ends and correctly sized clamps; small rated air fittings/hose, low-range regulator, downstream0–30psig gauge, bleed and independent relief. Reference line should fit the actual nipple (not yet measured); use reinforced vacuum/boost hose, not arbitrary aquarium tubing. No PVC compressed-air chamber ([OSHA](https://www.osha.gov/laws-regs/standardinterpretations/1991-02-28)); unrated exhaust tubing/welded caps do not establish a rated pressure assembly. `[recommendation based on hardware listing and web sources; unbuilt]`
- Diagnostic sequence once all fixture parts are rated: regulator starts at0; try1–2psig, then5psig, up to10psig only if needed and within every component rating. These are proposed diagnostic settings, not a proven safe maximum. Hold equal positive pressure on charge inlet/reference to check sealing, then isolate and lower reference toward vacuum while retaining inlet pressure to check opening/reseating. A combination hand pressure/vacuum pump provides reference control; small-volume hand-pressure testing alone suffices for wastegate rod movement. Do not use the seller25psi claim as a test target. `[recommendation; valve opening spec unknown]`

- Current wiring and I/O map: [WIRING.md](WIRING.md). INP1/A8=Spartan status; INP2/A9=oil transducer assignment. Oil monitoring saved enabled, protection Off, hardware/readback validation pending. `[user + tune: 2026-09-28]`
- Vehicle: 1999 Mazda Miata NB1, 1.8 L BP-4W, 1839 cc, 4-cyl, firing order **1-3-4-2**. `[user]`
- Forced induction: external **TD04L-13T** turbo. The build was rewire + turbo only; internals known-good (engine ran before the build). `[user]`
- ECU: **Speeduino UA4C, firmware 202501**. Saved configuration: speed-density, **Wasted COP**, **Semi-Sequential** injection, pairing "1+4 & 2+3". `[tune: CurrentTune.msq, 2026-09-28; burn status in STATUS.md]`
- **No factory instrument cluster.** The dash is TunerStudio on a Raspberry Pi, reading everything over the serial link — so tach-output settings (`tachoDuration`/`tachoMode`/`tachoDiv`) are irrelevant. `[user 2026-06-12]`
- Link: `/dev/cu.usbmodem101` @ 115200. A **data** USB cable is required — charge-only cables enumerate nothing. `[user]`
- Log tooling: `npx mlg-converter --format=csv <file>.mlg` → semicolon CSV in `DataLogs/`. `[user]`
- Hidden TS Hardware Test page: enable via `projectCfg/project.properties` (`enablehardware_test`). `[user]`

## The in-car dash Pi (DietPi)
- **Raspberry Pi 5, DietPi**, hostname `DietPi`, IP `192.168.1.134` (router DHCP reservation). SSH as **`dietpi`** (key auth installed 2026-08-16); `root` login does not accept that key. `[log 2026-08-16]`
- Runs **TSDash Pro 0.9.09.10** (`/home/dietpi/TSDash/TSDash.jar`). Config server: `http://192.168.1.134:16680` — the *only* scriptable way to change its settings. `[log 2026-08-16]`
- Boot chain: DietPi autostart index 17 → `/var/lib/dietpi/dietpi-autostart/custom.sh` (`startx -- -nocursor`) → `~/.xinitrc` (picom + Openbox) → `start-turboexo-session.sh` (MPV overlay) → **`start-turboexo-dash.sh`** → `TSDash.sh` → Java. Sources are versioned under `scripts/pi/`. `[src]`
- **Early native-resolution splash (installed 2026-09-07):** Debian Plymouth 24.004.60 runs from a 23,300,200-byte initramfs as soon as the VC4 KMS device is available. Its static script theme uses the exact same SHA-256-identical `exocet-boot-v10-root.png` as `feh`, with `DeviceScale=1` for a 1:1 1920×1280 canvas, no logo, text, cursor, spinner, progress indicator, or animation. `plymouth quit --retain-splash` preserves the last scanout while quiet tty1 autologin starts X. The existing `disable_splash=1` remains in `config.txt`, so the Raspberry Pi rainbow screen stays disabled. Sources and installer are under `scripts/pi/plymouth/`. `[src, log 2026-09-07; web: Debian Plymouth 24.004.60 manpages and source, https://manpages.debian.org/trixie/plymouth/plymouth.8.en.html, https://sources.debian.org/src/plymouth/24.004.60-5/]`
- **Fixed KMS timing and late-EDID finding:** the pre-change fresh boot did *not* maintain the assumed native mode: the kernel framebuffer was 1920×1280, but X started at 1024×768 because the panel's real EDID arrived only at ~140 s. The captured 256-byte EDID was stable across repeated reads and both 128-byte checksums are valid. It is embedded in initramfs and selected with `drm.edid_firmware=HDMI-A-1:edid/turboexo-1920x1280.bin`; `video=HDMI-A-1:1920x1280@60e` keeps the connector enabled. On the verified reboot, both KMS and X selected the EDID's preferred 164.82 MHz 1920×1280@60 timing from their first modeset; the prior rejected synthetic-mode warnings disappeared. `[log 2026-09-07; web: Linux EDID firmware and mode syntax, https://docs.kernel.org/admin-guide/edid.html, https://docs.kernel.org/fb/modedb.html]`
- **Measured early-splash timeline:** the reliable pre-change baseline was kernel entry 2.069 s → VC4 framebuffer 3.380 s → Xorg 5.011 s; the older empty-file markers, whose wall clock was later corrected by time sync, place feh root at ~8 s and MPV visible at ~10 s. On the clean attended boot ID `66a657e1-1cba-4e59-be3c-14c3ff553b3a`, initramfs unpack began 2.070 s, VC4 framebuffer was ready 2.090 s, Plymouth started 2.200 s and finished showing by 2.335 s, its retained exit completed 3.170 s, Xorg began 3.872 s, feh root completed 5.50 s, MPV became visible 6.73 s, TSDash HTTP-ready 11.00 s, dashboard-painted 17.98 s, and reveal completed 21.15 s. MPV-visible→painted was 11.25 s versus the prior 10.50 s benchmark. Firmware, HDMI link training, and kernel/KMS setup before about 2.3 s remain black; Plymouth and a direct-KMS client both require a Linux DRM device, so neither can cover that interval. `[log 2026-09-07; inference from measured first usable KMS/Plymouth timestamps]`
- **Plymouth installation and validation:** stage `scripts/pi/plymouth/` plus `assets/boot/exocet-boot-v10-root.png` on the Pi with their repository-relative paths, then run `sudo scripts/pi/plymouth/install.sh`. The guarded installer verifies the exact Pi/OS/kernel/display and artwork, backs up every target before modification, installs the Debian packages/theme/EDID/systemd files, enables future `raspi-firmware` initramfs generation, builds the current initramfs, and validates its content and boot copy without rebooting. Run `sudo turboexo-plymouth-validate` after kernel or boot changes. The systemd timeline observer writes exact milestones to `/run/turboexo-boot-timeline.log` and the journal without delaying tty1. `[src, log 2026-09-07; web: Raspberry Pi initramfs/config documentation, https://www.raspberrypi.com/documentation/computers/config_txt.html; systemd unit ordering, https://github.com/systemd/systemd/blob/main/man/systemd.unit.xml]`
- **Plymouth rollback:** installation `20260907T202343Z` has a complete root backup at `/var/backups/turboexo-early-splash/20260907T202343Z` and a boot-only recovery set at `/boot/firmware/turboexo-rollback/20260907T202343Z`. From a running Pi, `sudo turboexo-plymouth-rollback` restores the saved files, disables the still-installed Plymouth package with `plymouth.enable=0`, and does not reboot. If the Pi cannot boot, mount the FAT boot filesystem elsewhere and replace its root `config.txt` and `cmdline.txt` with the copies inside `turboexo-rollback/20260907T202343Z/`; that bypasses the initramfs, Plymouth, EDID override, and forced connector mode on the next boot. Use the recovery `cmdline.txt`, not `cmdline.original.txt`, for that first recovery boot. `[src, log 2026-09-07]`
- **X/MPV/TSDash handoff remains unchanged:** tty1 overrides systemd's delay-prone `Type=idle` with `Type=simple`, and DietPi's banner is suppressed. As soon as Xorg is usable, `feh` places `exocet-boot-v10-root.png` on the root window. MPV then loops the Pi-optimized `exocet-boot-loop-final-pi.mp4`, a 960×640/15 fps H.264 Constrained Baseline rendition upscaled to the native 1920×1280 display. It preserves the approved eight-second locked-car animation and exact decoded loop seam while reducing decoded pixels by 75%; MPV runs at nice level 10 to protect Java startup. The native 1920×1280 master remains `exocet-boot-loop-final.mp4`. Picom 12.5 uses XRender with no fullscreen unredirect. TSDash is mapped topmost and focused so X11 reports it unobscured and Java paints normally; picom makes every `ecuhubdash-EcuHubDash` window lacking `_NET_WM_WINDOW_OPACITY`, plus Java's classless native splash, transparent. MPV sits underneath and remains visible through those transparent windows. The wrapper waits for HTTP readiness and one second after `win0`–`win3` have all closed; the fallback is allowed only when no auxiliary window was ever observed. It then crossfades the main dashboard from transparent→opaque while MPV fades opaque→transparent over ten steps, leaves auxiliary windows hidden, and terminates MPV after the fade. After the Plymouth reboot, both overlay logs were empty, all markers appeared in order, MPV exited after reveal, and the 1920×1280 TSDash window remained topmost. `[src, log 2026-08-30, log 2026-09-07]`
- **TSDash updater restart handling:** the built-in `Staging.class` updater exits Java and relaunches the outer session wrapper. The wrapper gives a replacement `TSDash.jar` process up to 10 s to appear before recycling X; this keeps updater-driven restarts from being killed by Openbox teardown while genuine dashboard exits still restart tty1. `[log 2026-08-30]`
- **Hidden-paint A/B proof:** raw `xwd` captures of Java's 1920×1280 `Content window` at identical offsets compared production mode (MPV below + compositor-hidden TSDash) against a control with no MPV/opacity rule. Both began with the same white uninitialized buffer. Production mode had a complete gauge layout by 5 s and at 10 s was byte-identical to the control's normally visible 5 s buffer; it remained byte-identical through 65 s. Thus TSDash does paint while hidden. The former post-reveal loading was caused by premature timeout plus MPV continuously decoding hold frames, not Swing waiting for visibility. Freezing MPV eliminated that CPU load: production visible→painted was 10.50 s and visible→reveal 10.86 s. `[log 2026-08-30]`
- **Pi 5 Pi4J compatibility bridge (installed 2026-08-30):** TSDash 0.9.09.10 bundles Pi4J 1.3 with a 32-bit `libpi4j.so`, which fails on the aarch64 JVM with `ELFCLASS32`. `scripts/pi/pi4j-bridge/install.sh` builds Pi4J 1.4's JNI library for aarch64 against the already-installed Pi-5-capable WiringPi 3.16. The RP1 patch translates dynamic legacy-sysfs numbering; the virtual-input patch redirects exactly one environment-selected logical input while leaving all other pins on RP1. The result is isolated at `/usr/local/lib/turboexo-pi4j/libpi4j.so`; TSDash's JARs are unchanged. `[src, log 2026-08-30]`
- **Virtual key input:** the running Pi kernel has `CONFIG_GPIO_SIM` disabled but provides `gpio-mockup`. `turboexo-key-input.service` creates a one-line mock chip before the UPS monitor and tty1, discovers its dynamic sysfs GPIO, and exposes its root-owned pull control through `/run/turboexo-key-input/pull`. It defaults high so TSDash cannot pre-qualify a false key-off before the first monitor sample. The UPS monitor then writes high only for valid `connected` samples and low only for valid `discharging` samples; invalid I2C samples retain the last published state. No physical GPIO output or UPS/J2 change is involved. `[src, log 2026-08-30]`
- **Bridge loading:** `start-turboexo-dash.sh` supplies the isolated JNI library, resolves the RP1 gpiochip base, and reads `PI4J_VIRTUAL_BCM` plus `PI4J_VIRTUAL_SYSFS_GPIO` from the root-owned runtime environment. Logical BCM17 maps only to the simulated line. `dietpi` is a member of `gpio`. `[src, log 2026-08-30]`
- **Bridge validation and scope:** the high-level `GpioController` read both virtual states and received live LOW/HIGH callbacks in one JVM while physical RP1 GPIO17 remained unexported. After a clean boot, TSDash provisioned `KeyOnInput` as active-high with pull `OFF` and exposed the unique `AppEvent.ignitionOn` channel. `[src, log 2026-08-30]`
- **Bridge rollback:** disable `turboexo-key-input.service`, delete `KeyOnInput` in TSDash, remove the runtime virtual-input environment from the launcher, and restart tty1. The isolated library may remain installed while unused. `[src]`
- Live project on the Pi: `/home/dietpi/TSDashProjects/TurboExo_2026-06-01_21.16.20`. Serial `/dev/ttyACM0` @ 115200. `[log 2026-08-16]`
- **TSDash only reopens a project if `lastProjectPath` survives in `~/.efiAnalytics/tsdUser.properties`.** That key was simply *absent* — which is why it booted to the splash with no project, no gauges, no logging. The wrapper rewrites it before every launch, so an unclean power-down (every key-off in the car) can't strip it again. `[log 2026-08-16]`
- **TSDash 0.9.09.10 does NOT persist the Data Logging trigger config.** Every launch resets it to factory default (disabled, `tps > 80`, log-for 600 s) — a graceful SIGTERM does not save it either. The wrapper re-POSTs it to `127.0.0.1:16680` on each boot; success is logged to syslog as `turboexo-dash: triggered logging armed`. `[log 2026-08-16]`
- Logging is configured in Expression mode to start on `rpm > 0 && AppEvent.ignitionOn != 0`; stop requires an active log older than five seconds plus two seconds of `AppEvent.ignitionOn == 0`. This prevents a boot-time low from immediately stopping/restarting a new log. A clean-session regression test kept `2026-08-30_13.38.07.mlg` open past the start guard, then closed it when the virtual input went low without restarting TSDash. `[src, log 2026-08-30]`
- **Physical power-loss retest:** Python drove the simulated input low and the Pi subsequently completed its existing four-minute shutdown. No datalog was expected because RPM never became nonzero. Remaining acceptance is one solid crank followed by physical key-off, then conversion and source/USB hash comparison of that same log. `[log 2026-08-30]`
- Trigger channels: the Simple-mode channel dropdown accepts **ECU channels** (`rpm`, `batteryVoltage`, `tps`, …) but silently rejects `AppEvent.*` ones. Its condition dropdown renders empty (no `<option>`s) — `>` `<` `==` still POST fine. `[log 2026-08-16]`
- Uploading a project archive from the Mac re-introduces macOS paths (`/dev/cu.usbmodem*`, a `/Users/...` `logFileDir`). The wrapper rewrites both to `/dev/ttyACM0` and the Pi-local `DataLogs/` on every launch, so that trap is now self-healing. `[log 2026-08-16]`
- `sudo reboot` / `shutdown -r` fail on this box (`dbus-org.freedesktop.login1.service` is broken). Use `sudo systemctl reboot --force` — note that hard-kills TSDash. To restart just the dash: `sudo systemctl restart getty@tty1`. `[log 2026-08-16]`

## Trigger hardware
- NB1 99-00 crank and cam sensors are **open-collector Hall-effect** — not the NA's optical CAS, not VR. 3-wire each: A = 12 V switched, B = signal, C = ground. Crank = 4-tooth, cam = 3-tooth on the intake cam. `[web: Speeduino Miata 99-05 wiki, Haltech NB1 BP-4W docs]`
- UA4C jumpers, physically inspected 2026-06-17: JP2 (crank) = direct/Hall, JP3 (cam) = direct/Hall, JP4 (crank 1 k pull-up) = ON, JP5 (cam 10 k pull-up) = ON. Correct for these sensors. `[user 2026-06-17]`
- `TrigPattern` "Miata 99-05", `TrigEdge`/`TrigEdgeSec` RISING, `TrigSpeed` Crank Speed, `useResync` Yes, `perToothIgn` Yes. `[tune]`
- The 2026-06-20 dead-flat-0-RPM no-start was an **upstream wiring fault**, not the jumpers or the tune. Fixed; full sync since. The exact fault was never written down. `[user 2026-06-20]`

## Injectors & reqFuel
- **Installed now: OEM stock injectors** (swapped in 2026-07-19, replacing the RX-8 yellows). `[user 2026-07-19]`
- `reqFuel` **12.7 ms**, `injOpen` **1.0 ms**, `divider` 2, `multiplyMAP` Baro, `algorithm` MAP. `[tune]`
- 12.7 is the GitHub-verified factory value for this car (`speeduino/Tunes` → `Miata_PNP99-00_SpeedyEFI.msq`), and it is **12.7 in every revision of that file**. The local `~/Downloads` copy reads 14.7 only because TunerStudio re-saved it after a hand edit on 2026-04-03 — **never re-derive from the Downloads copy.** `[web: github.com/speeduino/Tunes commit history, checked 2026-07-11]`
- 12.7 confirmed live in the ECU on 2026-07-25 by back-solving PW (see below). `[log 2026-07-25_09.33.18]`

### Historical: RX-8 yellow injectors (removed 2026-07-19)
Kept only so old logs and old `.msq` snapshots can be read. Denso 195500-4450, 425 cc/min @ 43.5 psi, 11.8–16.5 Ω; stock 1999 "red" = Denso 195500-3310, 238 cc/min. Derived reqFuel for the yellows was 12.7 × 238/425 ≈ 7.0–7.1. Measured dead time at ~atmospheric: 14.0 V→0.55 ms, 12.75→0.70, 11.5→0.86, 10.25→1.15, 9.0→1.48, 7.75→2.02, 6.5→3.03. `[user]` **None of this applies to the currently installed OEM injectors.**

### Verifying the file matches the ECU
`PW = reqFuel/divider × VE/100 × MAP/100 × Gammae/100 + injOpen`. Pick any firing row
from a log and solve for reqFuel. Example (2026-07-25_09.33.18, VE 52, MAP 61,
Gammae 108, PW 3.18, injOpen 1.0) → reqFuel = 12.73. Do this before trusting any
`[tune]` value — editing a `.msq` on disk does **not** reach the ECU without a burn.

## Idle air — the current blocker
- `iacAlgorithm` = **PWM Open loop** (coolant-temp lookup only; **no RPM feedback at all**), `iacPWMdir` Normal, `idleFreq` 500 Hz, `iacFastTemp` −40 °F. `iacStepperInv` is present but is a stepper-only setting — no effect in PWM mode. `[tune]`
- `iacOLPWMVal` vs `iacBins`: 90 % @ −16.6 °F, 90 @ 19.4, 89 @ 42.8, 89 @ 60.8, 89 @ 77.0, 89 @ 95.0, 89 @ 114.8, **75 @ 154.4**, 75 @ 188.6, 75 @ 217.4. A 14-point cliff between two adjacent bins. `[tune]`
- `iacCrankDuty` 83 % flat. `[tune]`
- **The valve works and responds to duty.** In `2026-07-25_09.17.01` the engine idled closed-throttle (TPS 0) for **250 s**, and as coolant rose 82→127 °F the duty stepped 89→88→87→86→85 with idle RPM tracking it down 940→870→800 — monotone, ~30 rpm per duty point. `[log]`
- **Hot stall pattern**, same tune, 9 logs on 2026-07-25, sorted by coolant at death: 127 °F/89-85 % → idled 250 s · 131 °F/84 % → 0.6 s · 156 °F/75 % → none · 165 °F/75 % → 1.5 s · 171 °F/75 % → 0.7 s, dead. Once coolant passes ~155 °F the table commands 75 % and closed throttle stalls every time. `[log 09.17.01, 09.23.25, 09.28.44, 09.30.51, 09.33.18]`
- Stall shape (09.33.18): TPS 6→0 at t = 62.9 s, MAP 53→39 kPa, −1330 rpm/s, straight through 800 to dead in 1.4 s, IAC duty frozen at 75 the whole way. `[log]`
- Two aggravators: `idleAdvEnabled` = Off, so advance *retards* 19→16° as RPM sags instead of catching it `[tune + log]`; and the 500-rpm VE column (100–130 above 70 kPa, the deliberate cranking wall) means a recovery throttle blip floods it — PW went 2.6→4.9→9.84 ms at 708 rpm / 95 kPa. `[tune + log]`
- **Untested fix:** raise `iacOLPWMVal` rows at 154/188/217 °F from 75 toward ~88–90, add an intermediate bin, then move to Closed Loop PWM (~850 target). Consider idle advance ±5°. `[inference from the duty→RPM slope — not yet tried]`

## Wideband / AFR
- **Current hardware is the non-OEM Spartan replacement, with separate status wire.** The older Spartan 3 OEM module is no longer installed; do not apply its pinout. `[user: 2026-09-28]`
- The [Spartan 3 v2 manual](manuals/Spartan_3_v2_User_Manual_2026-01-21.pdf), page 1, documents the brown status wire: **0 V waiting, 1 V heating, 2 V heat-up complete / heater closed loop**. `GETNBMODE` reads its configured function (2=heater status). Exact installed revision has not been read back. Legacy manual and source hashes are in `docs/manuals/README.md`. `[web: 14Point7 manufacturer PDFs downloaded 2026-09-28]`
- Latest warm Aux0 is 565–604 counts. Nominal direct 10-bit/5 V conversion gives 2.76–2.95 V, not the manual's 2 V. Verify input transfer/brown-wire voltage or firmware status before decoding it. This does not prove unready; it also does not establish AFR calibration accuracy. Earlier OEM/model-conflict and LED-blink reasoning are superseded by the replacement confirmation and analog-status manual. `[log: 2026-09-28_13.29.24.csv; inference; web]`
- Cal is linear **0 V = 10.0 AFR, 5 V = 20.0 AFR**; sensor is LSU 4.9. `[tune + user]`
- Warmup output sequencer emits fixed cal voltages before the sensor is valid: ≈1.66 V = **13.3 AFR**, second plateau ≈3.33 V = **16.7** — the source of the pinned 13.1–13.2 / 16.4–16.5 in crank logs. `[web: 14point7]`
- **AFR echo:** `readO2()` always logs the raw sensor as AFR; `calculateAfrTarget()` returns live O2 as *Target* while `runSecs <= ego_sdelay`, and `runSecs` resets every crank. So on short catches Target shadows AFR and the pair is not mixture data. `[src: Speeduino 202501 sensors.cpp / corrections.cpp]`
- `egoType` Wide Band, `egoAlgorithm` No correction, `ego_sdelay` 15 s, `egoRPM` 1200, `egoTemp` 185 °F. `[tune]`
- **2026-07-25: AFR pegged at exactly 19.700 from t = 24.8 s to the end of the run, through big MAP and throttle swings** (and from t ≈ 51 s in 09.17.01). A pegged rail is a sensor/wiring fault or an un-heated sensor, not a mixture reading. There is still **no usable AFR data from any run.** Read plugs. `[log]`

## Knock
- The UA4C analog knock input has a **raw piezo sensor wired straight to it** — Speeduino needs a conditioned 0–5 V signal (TPIC8101 module or Phormula KS-4; band-pass ≈ 6.9 kHz for the 83 mm bore). `[user 2026-06-09 + web]`
- `knock_mode` = **Off**. `[tune]` Leave it off until a conditioner is fitted and the threshold calibrated at clean WOT.

## Ignition
- **Installed hardware: four Toyota/Denso 673-1300 / 90919-02239 COPs**, replacing the original Miata coil packs and plug leads. `[user: conversion recorded 2026-09-25, COP reconfirmed 2026-09-28]`
- Documented output wiring: **IGN1→cylinder 1, IGN2→3, IGN3→4, IGN4→2**. Cylinder 1 is at the timing-belt end. `[user: 2026-09-25, EXPERIMENT_LOG.md]`
- Saved mode **Wasted COP**, Going Low, crank/run dwell **4.0/2.5 ms**. These are current saved values, not verified Denso dwell specifications. Earlier Sequential configuration is historical. `[tune: CurrentTune.msq, 2026-09-28]`
- The following stock-coil electrical explanation and June timing check predate the COP conversion; they do not validate COP electrical behavior or current physical timing. `[user: conversion 2026-09-25; historical records below]`
- `IgInv` = **"Going Low"** — correct, do not change. Speeduino outputs are non-inverting (unlike MegaSquirt): rests LOW = coil off, HIGH to dwell, LOW to fire. The NB1 pack's internal igniter is HIGH = charge. "Going High" would rest with the coils energized and cook them. `[web: Speeduino Spark_Settings wiki, MSExtra coil-burn thread]`
- **Base timing confirmed good 2026-06-28 with a timing light.** NB 1.8 crank pulley has two marks 10° apart: WHITE = TDC, YELLOW = 10° BTDC — read the yellow. While cranking at a commanded 5°, yellow sat at ~6° → within 1°, `TrigAng` 0 correct. `[user 2026-06-28]`
- `CrankAng` 10°, `ignAlgorithm` MAP. `[tune]`

## Key tune constants (`CurrentTune.msq`, file dated 2026-07-19) `[tune]`
| Constant | Value |
|---|---|
| reqFuel / divider / injOpen | 12.7 ms / 2 / 1.0 ms |
| multiplyMAP / algorithm | Baro / MAP |
| battVCorMode | Whole PW |
| crankingEnrichTaper | 5.0 s |
| primePulse / primingDelay / fpPrime | 30/30/25/25 ms / 3.0 s / 5.0 s |
| CrankAng / crankRPM | 10° / 230 rpm |
| tpsflood | **60 %** (flood clear triggers above this) |
| engineProtectMaxRPM | **4000** |
| dfcoEnabled / idleAdvEnabled | Off / Off |
| stoich / mapMin / mapMax / baroPin | 14.7 / 3 / 416 kPa / A7 |
| fanSP | 201 °F |

## veTable format
- 16×16. **Rows = load** (`fuelLoadBins`: 20, 26, 30, 36, 40, 46, 50, 60, 70, 86, 100, 120, 140, 160, 180, 200 kPa); first listed row = lowest load. **Columns = RPM** (`rpmBins`: 500, 700, 900, 1500, 2100, 2900, …). `[tune]` Row orientation was confirmed by bilinear-fitting both orderings against 752–1177 logged `VE _Current` samples (mean error 0.4 vs 18.5 for the flipped reading). `[log]`
- The 500-rpm column is 100–130 above 70 kPa — a deliberate cranking-fuel wall, transplanted from the factory tune. It is also why a sagging engine floods (see Idle air). `[tune]`
- **Idle-vacuum trap:** forcing idle-region cells (500–700 rpm × 40–70 kPa) high makes the engine command ~2× fuel as MAP falls toward idle vacuum → floods, can't settle, MAP stuck near-atmospheric. The 07-10 crank-VE / crank-wall edits did this and were reverted. `[log]`

## Physical observations, unexplained
- **Plug read 2026-06-28 after cranking: cyl 1 dark, cyl 2 very dark and dirty, cyls 3 and 4 mostly clean.** `[user]` Injectors and coils are both paired 1+4 / 2+3, so a banked driver or coil fault would foul 1&4 or 2&3, not 1&2 — the pattern crosses both electrical banks. `[tune]` A clean strobe was seen off **#1**'s plug wire, so #1 sparks. `[user 2026-06-28]` **#2 has never been strobed, and no swap test was ever run.** Everything past this point (wire fault vs injector imbalance vs compression) is untested guessing — don't repeat it as a cause.
- These plugs predate the OEM injector swap. Re-read after a run before drawing anything from them.

## Resolved, don't re-litigate
- **MAP was plumbed to the MAC boost solenoid, not the manifold** — frozen dead-flat at 98–99 kPa across a whole 42 s log. Re-plumbed to manifold vacuum; MAP now moves (76–100 kPa cranking, down to 39 at closed throttle). `[log, before and after]`
- **VE table was factory × (100/load)**, which cancelled the MAP term with `multiplyMAP` on → ~2.9× factory fuel at idle vacuum. Replaced with a verbatim factory transplant for rows ≤ 100 kPa. `[log]`
- **Vacuum-leak-explains-cranking-MAP theory: dead.** Healthy cranking MAP is 80–95 kPa, so the logged 77–84 was normal. Leaks show up at warm idle (> ~40–45 kPa when 28–35 is expected), which is a check worth doing once it idles. `[web: DIYAutoTune, MSExtra]`
- **`engineProtectMaxRPM` 1500** sat right at the idle target and cut fuel + spark there. Now 4000. `[tune]`

## Open questions — genuinely unknown, do not guess
1. **Alternator resolved 2026-09-28:** Charging confirmed by 12.1 V before starting → 13.8–14.7 V running, without external charger/donor. `[log: 2026-09-28_13.09.03; user: 2026-09-28]`
2. **Spartan replacement:** Non-OEM controller with status wire confirmed; input voltage/status mapping remains to be verified. See Wideband. `[user + log: 2026-09-28]`
3. **Does #2 fire?** See Physical observations.
4. **Why is AFR pegged at 19.700?** Sensor, wiring, ground offset, or genuinely that lean — untested.
5. **What was the 2026-06-20 trigger wiring fault?** Never recorded.

## Tune file lineage
| File | What it is |
|---|---|
| `CurrentTune.msq` | the live tune — OEM injectors, reqFuel 12.7 (2026-07-19) |
| `TurboExo_FirstStart.msq` | first-start tune (WUE fatal-zero fixed) |
| `TurboExo_VEfix_2026-07-09.msq` | factory-transplant VE; the 07-09 catch to 1212 rpm; reqFuel 7.0, **on the old yellows** |
| `TurboExo_reqFuel85_2026-07-09.msq` | reqFuel 8.5 (refuted — too rich) |
| `TurboExo_crankVE_2026-07-10.msq`, `TurboExo_crankwall_2026-07-10.msq` | idle-region VE inflation — caused the idle-vacuum trap, reverted |
| `TurboExo_crankAdv10_2026-07-10.msq` | CrankAng 5→10 |
| `TurboExo_crankfuel_2026-07-11.msq`, `TurboExo_idleleanout_2026-07-11.msq` | yellow-injector reqFuel experiments (7.9, 7.1) — superseded by the OEM swap |
