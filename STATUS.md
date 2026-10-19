# TurboExo — Status (living)

Current wiring assignments: [docs/WIRING.md](docs/WIRING.md).

## 2026-10-19 — Boost-table import units warning corrected (disk only)

The October 18 change from Closed Loop to Open Loop retained the old `boostTable`
units attribute. The local mainController.ini selects Duty Cycle % for Open Loop.
Corrected only `units="kPa"` to `units="Duty Cycle %"` in CurrentTune and
`TurboExo_boost_table_preparation_PROVISIONAL_2026-10-18_202332.msq`.
Preserved timestamped pre_units_fix copies and refreshed the prepared file checksum.
Verified XML parsing and byte equivalence apart from that label; all 64 cells remain
zero, boost output remains Off, and the two corrected files match exactly.
TunerStudio re-import and ECU readback remain unverified; no ECU write performed.

## 2026-10-18 — Provisional boost-table preparation (disk only)

Successful hot-running/AutoTune baseline preserved before edits:
`TurboExo_SUCCESS_hot_idle_autotune_pre_boost_extension_2026-10-18_202332.msq` (checksum/provenance alongside).
Prepared load file: `TurboExo_boost_table_preparation_PROVISIONAL_2026-10-18_202332.msq`; CurrentTune matches.
VE/AFR/ignition now cover200kPa with preserved learned idle cells and provisional
boost rows; omitted-bin interpolation changes are quantified in `.changes.json`.
This is table coverage, not validation or permission to operate at200kPa.

Boost output explicitlyOff, OpenLoopzero duty; meaningful RPM/TPS axes prepared.
Protection RPM gate corrected7000→1500; boost cut retained120kPa absolute
(~3psi gauge at99kPa baro), SparkOnly. This gate had prevented protection below
7000RPM; legacy Boost cut log flag alone is not reliable evidence of activation.
Normal rev-limit settings, reqFuel12.6, Sequential modes and idle tables preserved.
Load/burn/power-cycle/readback pending; no ECU changes made by assistant.

User's generic25mm atmospheric BOV and35A-AAA-DDBA-1BA solenoid seller listings
saved under docs/hardware; port routing and pressure response unverified.
Intended boost target remains unspecified. Bench-test plan in docs/REFERENCE.md;
latest EXPERIMENT_LOG.md records exact changes and unresolved items.

## 2026-10-18 — AutoTune run: fully warm idle confirmed

14:21:46 log holds running for~450s, including final30s closed throttle at
1380–1467RPM,31–33kPa,199–201°F, IAC77%. Zero sync losses; charging-range voltage.
Logged idle AFR median13.8 versus14.2 target; no dominant warmup echo, but sensor
calibration is still not independently validated. Idle remains above850RPM target.
CurrentTune differs from running milestone in103 VE cells; no other ECU constants
changed. Post-AutoTune disk capture: `TurboExo_autotune_hot_run_2026-10-18_142146_DISK.msq` plus checksum.
Original running milestone retained. Neither snapshot is independent ECU readback.
Run reaches136kPa; fuel-load axis still ends100kPa. Boost calibration remains open.
See newest EXPERIMENT_LOG.md entry; fully hot idle is now demonstrated.

## 2026-10-18 — RUNNING milestone: sequential scaling fixed, idle confirmed

User confirms runs but needs throttle to start. Latest14:10:18 log confirms
131.9s continuously above700RPM, still running at end, closed-throttle idle,
charging-range battery voltage and zero recorded sync losses. Final30s:
RPM995–1144, TPS0–0%, MAP43–47kPa. CLT reaches151°F; fully hot idle not yet established.

Preserved disk milestone: `TurboExo_running_sequential_fuel_scaling_fixed_2026-10-18_141358.msq`
with SHA256 and provenance sidecars. Current saved settings: reqFuel12.6,
one squirt/divider4, Simultaneous staging, Sequential injection and ignition,
TrigAng0. Cranking IAC is now99% (logged98–99%), running open-loop table also
changed; end-of-log IAC82%. Plugs cleaned before testing. Full ECU readback
and physical coil-phase swap remain unconfirmed. No tune edits by assistant.
Remaining objective: resolve throttle-assisted starting, then validate hot idle.
See latest EXPERIMENT_LOG.md entry. This supersedes the pending/no-idle results below.

## 2026-10-18 — Fuel restored; corrected sequential scaling ready for test

User found tank apparently empty (sender110ohms), added fuel, then reported
starting attempts and wet plugs. Latest analyzed log13:46:14 peaks727RPM without
settled idle; initial cranking commands49–54ms. Full throttle was intentional.

User has now selected Simultaneous staging with one squirt, retained upper
required-fuel12.6, cleaned all plugs and restarted ECU. CurrentTune confirms
saved reqFuel12.6 (was25.2), divider4, Simultaneous and Sequential injection.
TunerStudio had calculated25.2 from upper12.6 with one squirt/Alternating;
firmware already compensates sequential pulse size. Expected PW under matching
conditions is roughly25–27ms. ECU readback remains unverified. Post-change14:03:45 log confirms median
closed-throttle cranking PW20.546ms (previous49.460ms), with total correction
also down212→170%. Peak622RPM; catches at closed/slight throttle but no settled
idle. Zero sync losses; AFR still echoes target. Both logs have timestamp resets.
IAC is connected per user; current disk cranking duty remains83%.
See latest EXPERIMENT_LOG.md entry. Older named sequential test files below
predate this correction; do not treat them as the current test tune.

## 2026-10-18 — Pi automatic shutdown temporarily disabled

Removed `--poweroff` from the live and repository `pi-ups-monitor.service` at
user request. Restarted only the monitor; it remains enabled for key-state
monitoring. Verified running command has no `--poweroff`. This persists across
reboots until explicitly reenabled. Live backup:
`/etc/systemd/system/pi-ups-monitor.service.before-disable-20261018`.
Before the change the monitor reported discharge at -0.423 A / 11.324 V.
This disables the software four-minute shutdown, not hardware power loss.

## 2026-10-18 — Full sequential 0° with proposed coil phase swap

User confirms the +360° full-sequential tune was loaded and burned, but engine
would not run. This is a user-reported result; ECU readback was not independently
verified. User selected 0° with both ignition and injection Sequential, superseding
the intermediate request for Semi-Sequential injection.

Changed only TrigAng +360→0 in the latest CurrentTune and named test file.
Preserved newer TunerStudio settings, including reqFuel25.2ms and divider4;
compared constants against the two latest October18 restore points before editing.
Both sparkMode and injLayout remain Sequential. XML parsing and full constant
comparison verified TrigAng is the sole change.

Proposed physical ignition map for this test: IGN1→cylinder4, IGN2→2,
IGN3→1, IGN4→3 (swap cylinder1/4 and2/3 coil signal assignments with power off).
Physical swap is not confirmed performed. Injector wiring remains INJ1→1,
INJ2→3, INJ3→4, INJ4→2. Thus this changes ignition phase relative to the original
0° mapping, while injection stays at its original 0° phase.

Test load: `TurboExo_sequential_zero_coilswap_TEST_2026-10-18_121049.msq`.
Immediate disk backup: `TurboExo_pre_sequential_zero_coilswap_TEST_2026-10-18_121049.msq` (the unsuccessful +360° configuration,
not a known-running rollback). CurrentTune matches the test file.
Disk preparation only: load/burn, power-cycle, verify settings, then one short
logged crank ≤5 seconds. No ECU write or result for this new test verified.

## 2026-10-17 — Full sequential opposite-phase diagnostic (+360°)

User requested online research and starting from the hypothesis that full
sequential phase is360° out. Researched official Speeduino202501.7 Miata99-05
decoder and independently reviewed scheduler/crank-lock behavior. Changed only
TrigAng0→+360 degrees; ignition and injection remain Sequential. Fuel quantities,
injection angle355, crank lockOn, cranking advance10, dwell and wiring unchanged.

Source inference: getCrankAngle adds offset and wraps at720; both sequential
schedulers consume that angle. Locked cranking ends coil pairs1+3/2+4 on fixed
teeth, but charging starts are individually scheduled and therefore shift the
energized member by360. A positive360 offset flips both stroke assignments while
retaining nominal fixed-tooth10° firing. Negative360 is NOT equivalent in this
decoder because its negative normalization only adds360.
Important test limitation disclosed: Miata per-tooth correction requires
triggerAngle==0; +360 bypasses it and uses scheduled ending after crank lock.
This is a short diagnostic, not validated permanent or driving calibration.
No-start alone does not confirm phase error. Research sources:
https://github.com/speeduino/speeduino/blob/202501.7/speeduino/decoders.cpp
https://github.com/speeduino/speeduino/blob/202501.7/speeduino/speeduino.ino
https://github.com/speeduino/speeduino/blob/202501.7/speeduino/scheduler.cpp

Rollback (full sequential0°): `TurboExo_pre_sequential_phase360_TEST_2026-10-17_144758.msq`.
Test load: `TurboExo_sequential_phase360_TEST_2026-10-17_144758.msq`; CurrentTune matches. XML parsing, full constant
comparison (only TrigAng) and exact byte checks passed. Disk only; load/burn and
fully power-cycle ECU to establish sequential modes, then one short logged crank.
No ECU write or phase-test result verified.

## 2026-10-17 — Full sequential ignition AND injection test

User clarified that intended test includes both injector and ignition wiring,
then explicitly directed completing it. Supersedes ignition-only staged test.
Current sparkMode already Sequential; changed only injLayout Semi-Sequential
→Sequential. Both modes now Sequential. Preserved reqFuel12.6ms, divider2,
injAng355deg, all fuel/ignition tables, trigger settings and all other constants.
Confirmed physical output order for BOTH systems remains1→cyl1,2→3,3→4,4→2.
No phase offset changes.
Backup of immediate ignition-only state: `TurboExo_pre_full_sequential_TEST_2026-10-17_144437.msq`.
Full test load: `TurboExo_full_sequential_TEST_2026-10-17_144437.msq`; CurrentTune matches. Original pre-test
Wasted COP/Semi-Sequential rollback remains
`TurboExo_pre_sequential_ignition_TEST_2026-10-17_144208.msq`.
XML parsing, full constants comparison and byte verification passed. Saved only;
load/burn/full ECU power cycle (including USB/backfeed) required for both modes.
No ECU write or starting result verified.

## 2026-10-17 — Sequential ignition comparison requested

User explicitly wants to try sequential ignition and suspects its cam-phase
assignment may land on the wrong stroke. Saved current Wasted COP baseline,
then changed only sparkMode Wasted COP→Sequential in CurrentTune.msq and
explicit test file. Injection remains Semi-Sequential, output pairs1+3/2+4.
Preserved current individually tested coil order IGN1→cyl1,2→3,3→4,4→2;
trigger angle0, crank lockOn, cranking advance10deg, dwell4.0/2.5ms and all fuel.
Experiment compares ignition scheduling modes; no-start alone would not prove
360-degree phase error. No phase offset or physical wiring change performed.

Rollback: `TurboExo_pre_sequential_ignition_TEST_2026-10-17_144208.msq`. Test load: `TurboExo_sequential_ignition_TEST_2026-10-17_144208.msq`.
XML parsing, complete constants comparison (only sparkMode), backup and output
byte checks passed. Disk only. INI requires power cycle for sparkMode: load and
burn, fully remove ECU power including USB/backfeed, then reconnect and verify
Sequential before one short logged crank. No ECU write or test result yet.

## 2026-10-17 — Revert scheduled cranking timing test

User requested reverting the timing test after the 14:26 log showed no start.
Restored only CrankAng to 10° and ignCranklock to On from the pre-test backup.
All other current constants preserved. Backup: `TurboExo_pre_revert_crank_timing_2026-10-17_142902.msq`.
Explicit load file: `TurboExo_crank_timing_reverted_2026-10-17_142902.msq`. XML, full constant comparison and byte
verification passed. Disk only; ECU burn/readback pending. Supersedes the 5°
unlocked test.


## 2026-10-17 — Scheduled 5° cranking timing test

User requested only CrankAng 10→5° and ignCranklock On→Off to test later
cranking spark after reported kickback. Preserved all other latest saved constants,
including newer changes relative to the 13:45 restore point.
Backup: `TurboExo_pre_crank_timing5_unlocked_2026-10-17_142233.msq`. Explicit load file: `TurboExo_crank_timing5_unlocked_2026-10-17_142233.msq`.
XML and full constant comparison passed; only those two constants changed.
Disk-only edit; ECU burn/readback and start result remain unverified.


## 2026-10-17 — Restore deceleration fuel amount to100%

User explicitly requested decelAmount100%. Previous saved value:0.0%.
Changed only decelAmount to100%, retaining normal fuel during qualifying TPS
deceleration events instead of a zero-percent fuel cut. No maps, wiring,
acceleration-enrichment method or other settings changed.
Backup: `TurboExo_pre_decel100_2026-10-17_140649.msq`. Explicit load file: `TurboExo_decel100_2026-10-17_140649.msq`;
CurrentTune.msq matches. XML, complete constants comparison and exact backup/output
byte verification passed. Disk only; load/burn/readback pending. No ECU write
or new start test performed; effect on the starting problem remains untested.

## 2026-10-17 — Recover filters, TPS endpoints and crank-to-run fuel taper

User identified these reset differences for recovery and confirmed TPS27/185
came with the reset, not a new measurement. Restored from October10 reverted
baseline: TPS28/127; crankingEnrichTaper0.1→5.0s; filters TPS50,CLT180,IAT180,
O2 128,battery128,MAP20,baro64 (all previously zero). TPS physical closed/full
travel still needs checking; recovered values are historical calibration.
Preserved verified new injector/ignition wiring settings, oil/status inputs,
all maps, enrichment curves and PW Adder. Independent map reviews found near-identical atmospheric cranking values, but
a 40% VE reduction at500rpm/66kPa and lost boost table coverage. See latest
EXPERIMENT_LOG.md entry; maps remain unchanged.
This is recovery of selected baseline settings, not proof of a no-start cause.

Backup: `TurboExo_pre_filters_TPS_taper_recovery_2026-10-17_140406.msq`. Explicit load: `TurboExo_filters_TPS_taper_recovered_2026-10-17_140406.msq`; CurrentTune matches.
XML parsing, complete constants comparison (only10 expected changes), and
backup/output byte verification passed. Disk only: load/burn/readback pending;
no ECU write or new start test performed.

## 2026-10-17 — Reset reviewed; oil/status inputs repaired on disk

User reset the tune and requested oil-pressure repair. The 13:37:57 save assigned
native oil pressure to A8 with -8/117 psi endpoints, while Aux0 read A9 and was
labeled OilPressure. Documented wiring is Spartan status on INP1/A8 and the
0.5-4.5 V / 0-100 psi oil transducer on INP2/A9.

Changed only four ECU constants and one PC alias: oilPressurePin A8 -> A9,
oilPressureMin -8 -> -13, oilPressureMax 117 -> 113, Auxin0pina A9 -> A8,
and AUXin00Alias OilPressure -> Aux0. Oil monitoring remains On and protection
Off. All unrelated reset settings were preserved.

Backup: `TurboExo_pre_oilpressure_fix_2026-10-17_134104.msq`.
Explicit load file: `TurboExo_oilpressure_fixed_2026-10-17_134104.msq`;
CurrentTune.msq matches at completion. XML, complete constant/PC-variable
comparison, exact backup and byte-identical load-file checks passed.
Saved on disk only: open the explicit file in TunerStudio, burn, fully power-cycle
the ECU (including USB power), and verify readback. No ECU write or independent
pressure measurement was performed by this repair.

Reset review found 114 constant differences (including six added constants)
versus the October 10 confirmed-running disk milestone before the oil repair.
Cranking enrichment is now flat 125%; WUE/ASE/VE differ; TPS endpoints are 27/185;
all seven ADC filters are zero. Fuel, ignition and AFR load axes stop at 100 kPa.
Closed-loop boost is enabled with zero targets and degenerate bins. These need
review before calibrated boost operation; they were not changed here. Zero boost
targets disable control in the inspected firmware, so do not infer an 85%
solenoid command. Latest local log 12.04.50 predates the broad reset saves and
does not validate the reset's running behavior.

Core saved settings remain UA4C, Semi-Sequential output pairing 1+3/2+4,
Wasted COP, Going Low, Miata 99-05, offset 0, crank lock On, cranking advance 10,
and cranking threshold 400. User hardware testing confirms BOTH injector and
coil outputs 1 -> cylinder 1, 2 -> 3, 3 -> 4, 4 -> 2. IAC remains unplugged.
Actual cranking timing is still unmeasured in this session; user reports stumbling
and an intake pop with starting fluid.

## 2026-10-11 — Bluetooth recovered after disconnecting backfeeding light

User found voltage backfeeding from a light, disconnected it, reported Bluetooth
improved, then confirmed “all fixed.” Recovery is user-confirmed; no independent
post-fix Pi telemetry check was performed in this session. Exact light, circuit,
backfeed voltage/path and permanent wiring remedy remain undocumented.

Before the fix, Pi TSDash was running and retrying /dev/rfcomm0 at 115200, but
Bluetooth was disconnected and ECU identification timed out; the module LED was
dark. Pi and laptop saved tunes retained 12.7 ms / Semi-Sequential / Wasted COP.
Direct USB ECU readback independently confirmed firmware Speeduino 2025.01.7 and
those three settings. Live telemetry returned zero error flags/error byte, RPM 0,
and battery voltage 3.4 V before the user turned the key on, then 12.0 V afterward.
These are ECU-reported readings, not multimeter measurements or proof of module
supply voltage. No tune writes were made by this diagnostic session.

The initial difference dialog showed 6.9 ms / Paired on its controller side, but
its provenance was not established; the later direct readback did not show those
values. Do not infer a tune reset from that dialog or from an offline Pi. This was
not a full tune comparison or a power-cycle persistence test. See the October 11
entry in EXPERIMENT_LOG.md and the power/backfeed note in docs/WIRING.md.

## 2026-10-10 — Undo warm-start cranking-fuel test

User requested undoing our changes after the14.23.31 warm-start log did not
show a sustained start. Restored crankingEnrichValues from
TurboExo_pre_warm_crankfuel_2026-10-10_142252.msq: 225.0 195.0 175.0 95.0
→225/195/175/125%. Earlier whole-curve reduction was already reverted.
Preserved all other current constants, including temperature bins.
Backup: `TurboExo_pre_undo_warm_crankfuel_2026-10-10_142735.msq`. Explicit load file: `TurboExo_warm_crankfuel_reverted_2026-10-10_142735.msq`;
CurrentTune.msq matches. XML, complete constant comparison and exact byte checks
passed. Saved on disk only; load in TunerStudio, burn and verify readback.
No ECU write or new start test performed. Supersedes warm-start reduction.

## 2026-10-10 — Warm-start cranking-fuel test; cold curve preserved

User confirms earlier successful start was cold; latest 14.16.04 log at136°F
shows catches/rotation but no sustained run. IAC remains unplugged. User authorizes
a targeted warm cranking-fuel reduction. Rich warm starting remains a hypothesis.
Changed only final crankingEnrichValues entry125→95%; first three remain
225/195/175%, with all bins unchanged (−38.214/33.786/89.586/181.386°F).
Four-point interpolation gives approximately150→135% at136°F (~10% less);
the curve at/below89.586°F is unchanged. Reduction grows toward the hot endpoint:
181.386°F and above now95% versus125% (24% lower), an unvalidated hot-start
setting. This scope was disclosed before editing. Priming, WUE, ASE, taper,
running VE and ignition unchanged.

Backup: `TurboExo_pre_warm_crankfuel_2026-10-10_142252.msq`. CurrentTune.msq and explicit test load file
`TurboExo_warm_crankfuel_TEST_2026-10-10_142252.msq` match. Compared current constants with newest restore and preserved
all unrelated settings. XML parsing, complete constant comparison and byte checks
passed. Saved on disk only; open test tune in TunerStudio, burn and verify readback.
No ECU write or start test performed; compare near136°F. Running milestone preserved.

## 2026-10-10 — Revert cranking fuel reduction

User requested reverting the preceding cranking-enrichment reduction. Restored
crankingEnrichValues to 225/195/175/125% from the pre-reduction backup, preserving
all other current constants. Prior values: 225.0 195.0 175.0 125.0.
Backup: `TurboExo_pre_crankfuel_revert_2026-10-10_140616.msq`. Explicit load file: `TurboExo_crankfuel_reverted_2026-10-10_140616.msq`;
CurrentTune.msq matches. XML, full constant comparison and byte verification
passed. Saved on disk only; ECU burn/readback and start result unverified.
This supersedes the reduction below; no reason or test result was supplied.

## 2026-10-10 — Cranking fuel reduction for throttle-assisted starting

User confirms IACV is unplugged and a little throttle is needed to catch, but
can release it immediately and engine idles. Excess cranking fuel is a hypothesis,
not a confirmed diagnosis. User requests the discussed 10% cranking-enrichment
reduction. Firmware INI stores this curve in 5-percentage-point steps; nearest
representable values (ties rounded up): 225/195/175/125 → 205/175/160/115%,
at unchanged −38.214/33.786/89.586/181.386°F bins. Actual reductions are
8.9/10.3/8.6/8.0%; exact 10% is not representable.

Changed only crankingEnrichValues in CurrentTune.msq. Preserved newer current
constants after comparison with newest restore point. Backup: `TurboExo_pre_crankfuel_reduction_2026-10-10_135514.msq`.
Explicit load file: `TurboExo_crankfuel_reduction_2026-10-10_135514.msq`. Running ignition-fix milestone preserved.
XML parsing, full constant comparison, backup and output byte checks passed.
Saved on disk only; load in TunerStudio, burn, and verify readback. No ECU write
or start test performed. Compare starts at similar coolant temperature; result pending.

## 2026-10-10 13:58 — Boot fix and recovery tested; Mac TunerStudio errors

First controlled Pi reboot: hotspot/AP/DHCP started, but Bluetooth bind failed
with "Protocol not supported" because rfcomm had only been loaded manually.
Fixed deployed turboexo-bluetooth-serial.service with ExecStartPre modprobe rfcomm,
3-second failure retries, and no start-rate limit. Pi launch wrapper now restores
/dev/rfcomm0, 115200 and Bluetooth Port=true even after Mac project imports.
Fixture import/idempotence and shell syntax checks passed; independent review
found no substantive blocker. Both deployed files mirror scripts/pi sources.

Second controlled reboot (boot dcbbc00a-36f0-47ae-a9ae-f8652223086b): all four
hotspot/Bluetooth units active; AP-ENABLED and DHCP on ap0; Bluetooth connected
and TSDash resumed telemetry automatically. User confirmed SSID visible after
first reboot. Deliberate Bluetooth disconnect recovered connected/tty-attached
in about 14 seconds monotonic elapsed; fresh ECU telemetry then confirmed.
Automatic logging remains enabled. No calibration changes by this work.

Mac TunerStudio reconnected through home Wi-Fi/Dash Echo, but its log then showed
StackOverflowError in AWT, clock and XCP threads at about 13:57:44 onward.
Pi continued transmitting telemetry. Mac application restart and live-gauge
verification needed before calling the complete AutoTune session ready.
Full power-off boot away from home, long driving stability and tuning writes
remain untested. Keep ECU USB disconnected for this Bluetooth configuration.
Rollback now also requires restoring the Pi launcher from
/home/dietpi/TSDash/start-turboexo-dash.sh.before-bt-boot-20261010 before restoring
USB project settings; otherwise the launcher will reassert Bluetooth.

## 2026-10-10 13:54 — Pi Bluetooth to ECU; Mac Dash Echo working

Pi paired with Speeduino08203 (00:0C:BF:0A:35:72). Direct RFCOMM channel 1
identification returned F=`002`, Q=`speeduino 202501`, with ECU USB unplugged.
Changed Pi TSDash serial port from /dev/ttyACM0 to /dev/rfcomm0 at 115200,
Bluetooth Port=true. Continuous telemetry verified after two dashboard starts.
Installed/enabled turboexo-bluetooth-serial.service to bind the port at boot;
service startup verified, full cold boot and driving stability remain untested.
Mac TunerStudio subsequently read controller pages with matching checksums at
13:53:36 via Dash Echo; Pi shows its TCP client connected on 21848.
Use home Wi-Fi endpoint 192.168.1.134:21848 to retain Internet during agent work.
TurboExo hotspot endpoint remains 192.168.50.1:21848; joining it loses Mac Internet.
No ECU calibration changes made. USB fault and Mac direct-Bluetooth fault remain
unresolved; this connection path bypasses both.

Rollback: stop getty@tty1 on Pi; restore projectCfg/project.properties from
project.properties.before-bluetooth-20261010 in the same Pi project directory;
disable/stop turboexo-bluetooth-serial.service; reconnect ECU USB and start
getty@tty1. Backup directory: /home/dietpi/TSDashProjects/TurboExo_2026-06-01_21.16.20.

## 2026-10-10 — Ignition wiring corrected; car runs (user confirmed)

User confirmed that correcting the physical COP connections to **IGN1 → cylinder 1,
IGN2 → cylinder 3, IGN3 → cylinder 4, IGN4 → cylinder 2** restored running.
Cylinder 1 is at the timing-belt end. In saved Wasted COP mode, IGN1+IGN3 fire
cylinders 1+4 together; IGN2+IGN4 fire cylinders 3+2 together.
The previous physical connection order was not established. Earlier documentation
of the intended map did not prove that the harness actually matched it.
This supersedes the unresolved wiring/phase discussion and any claim that earlier
catches proved the physical output map. Voltage was a diagnostic lead, not an
established cause of this failure. User-reported running does not itself establish
measured base timing or a new road test.

**Preserved tune:** [TurboExo_running_after_ignition_wiring_fix_2026-10-10_131234.msq](TurboExo_running_after_ignition_wiring_fix_2026-10-10_131234.msq), copied byte-for-byte
from CurrentTune.msq at 13:12:34 PDT (TunerStudio save: 13:08:16 PDT).
SHA-256 and provenance are in the adjacent `.sha256` and `.json` files.
Snapshot XML and exact bytes were verified. Saved values: Wasted COP; Miata 99–05;
trigger angle 0°; cranking advance 10°; Going Low; rising primary/secondary edges;
crank/run dwell 4.0/2.5 ms; crankRPM 300; Semi-Sequential; reqFuel 12.7 ms.
Compared with today's 11:36:32 restore point, only veTable differs among constants;
the newer table was preserved, not replaced. No tune settings were changed here.
This is the current disk tune preserved at the time of confirmed running, not an
independently verified ECU readback. Keep this milestone separate from historical
July “last-known-good” files; do not overwrite it with an older tune.

## 2026-10-10 — Pi tuning hotspot enabled alongside home Wi-Fi

Implemented `TurboExo` AP (`ap0`, 192.168.50.1/24) beside home `wlan0`.
Both share channel40; station scanning/selection is restricted to5200MHz with
30s automatic retries. Dash Echo already worked and remains on21848; web16680.
Three dedicated hotspot services are active/enabled. Generated credential stays
in root-readable /etc/turboexo/wifi/hostapd.conf, not Git. No NAT/default gateway.
Mac was returned to home Wi-Fi for Internet; join TurboExo to use192.168.50.1:21848.

First trial's apparent reconnect failure was a test bug: SET_NETWORK bssid with
all-zero MAC pins that address. Corrected restore uses any and verifies GET returns
its original unset state. Corrected loss/return:76/76 hotspot checks passed, home
reconnected automatically in about26s. Fresh AP start while home unavailable:
72/72 checks passed, home reconnected automatically in26.06s. TunerStudio connected
through the hotspot; the later offline event followed deliberate AP shutdown for
Mac return. Full cold boot away and sustained driving/sleep remain untested.

Sources/config, validation and rollback are in scripts/pi/wifi/ and
 docs/PI_WIFI_HOTSPOT_PLAN.md. Live rollback:
/var/backups/turboexo-wifi/20261010T190927Z/rollback.sh. No rollback/test timers remain.
No ECU tune, TSDash, logging, or UPS configuration changes were made by this work.

## 2026-10-10 11:40 — Sustained run; cylinder 4 temperature deficit reported

Reviewed newest local `DataLogs/2026-10-10_11.40.53.mlg` and generated its CSV.
Pi SSH connection timed out; no new remote file was retrieved. Discard first
time-zero placeholder (battery0, CLT-40); coherent log27.743–57.210s (29.467s).
Engine runs throughout and ends1453rpm, TPS7%, MAP63kPa, battery14.4V, CLT109°F.
Initial27.743–34s median1080rpm, MAP65kPa, TPS4%, battery14.5V. Later throttle
events reach2958rpm and112kPa against98kPa baro. No captured shutdown.
Logged PW1=PW2 in all441 coherent rows; PW3/PW4 zero does not establish dead
physical injectors in Semi-Sequential mode. AFR differs from target but cannot
resolve fueling versus misfire; no global fueling change derived.

User reports cylinder4 approximately200 degrees cooler and cylinder2 somewhat
cooler but harder to assess. Units, measurement location and matched readings
remain unconfirmed. This is evidence to investigate cylinder contribution, not
proof either cylinder never fires. Documented cyl4 usesIGN3/INJ4; cyl2 usesIGN4/INJ2.
Firmware202501.7 init.cpp confirms Wasted COP schedules physical IGN1+3 and2+4,
and Semi-Sequential schedules INJ1+4 and2+3. All four physical outputs are included
by these modes; suspect cylinders are in different pairs. Check cylinder4 coil,
plug and actual ignition output first, then injector delivery/compression as needed.

Latest CurrentTune matches the requested restored VE table. Compared with the
11:23 rollback, only battVCorMode now Open Time only and boostType now Open Loop
differ. These are observed TunerStudio saves, not changes made in this analysis;
ECU readback remains unverified. No tune edits performed.

## 2026-10-10 — Reapply requested 18-cell VE rollback

User requested reverting the increased VE cells found during the base-map review.
Fresh CurrentTune matched the October 4 17:28:10 restore, with all 18 increases
present again. Restored only veTable from
`TurboExo_VE_rollback_2026-10-04_171644.msq`; RPM/load axes already matched.
All other 806 constants preserved, including Whole PW battery compensation.
Backup: `TurboExo_pre_VE_rollback_2026-10-10_112328.msq`.
Explicit load file: `TurboExo_VE_rollback_2026-10-10_112328.msq` (identical to CurrentTune at verification).
XML parsing, full constant comparison, exact reference VE match, and byte
verification passed. Saved on disk only; load the named file in TunerStudio,
burn and verify readback. ECU application and running result remain unverified.
The reverted cells are at 900–2100 RPM; they do not explain the latest log's
failure to exceed 410 RPM. No battery-compensation change was requested or made.

## 2026-10-04 — VE rollback restored after TunerStudio overwrite

At 17:16:30 TunerStudio saved the increased VE table back into CurrentTune.
The 17:15:20 reload logged zero bytes updated; subsequent burn was skipped because
no writes had occurred. Rollback was not applied by that sequence.
Restored the same 18 VE cells again, preserving every other constant, and created
`TurboExo_VE_rollback_2026-10-04_171644.msq` for explicit loading without relying on CurrentTune surviving autosave.
Backup: `TurboExo_pre_VE_rollback_retry_2026-10-04_171644.msq`. XML and full constant diff passed; only veTable changed.
Verified CurrentTune and named rollback are identical and match the 10:31 VE table.
ECU burn/readback remains pending. Load the named rollback file in TunerStudio.

## 2026-10-04 — Restore VE map to today's 10:31 AM snapshot

User requested undoing the identified map changes. Snapshotted latest CurrentTune
as `TurboExo_pre_VE_rollback_2026-10-04_171421.msq`, then restored only `veTable` from
`restorePoints/TurboExo_2026-10-04_10.31.19.msq`: 18 increased cells reverted.
All other 806 constants preserved, including flood-clear TPS 80% and fan setpoint
190.386°F. XML parsing, complete constant comparison, exact reference VE match,
and snapshot/write byte verification passed. No running result yet.
Saved on disk only; reload CurrentTune in TunerStudio before burn/readback.
ECU application is unverified; this rollback does not establish a stall cause.

## 2026-10-04 — Pi logging and automatic shutdown reenabled

User requested logging now and restoration of both automations. Live TSDash at
192.168.1.134:16680 now confirms Automatic Triggered Logging enabled, with start
`rpm > 0 && AppEvent.ignitionOn != 0` and stop
`AppEvent.dataLogTime > 5 && isTrueFor(AppEvent.ignitionOn == 0, 2)`.
Updated both repository and deployed start-turboexo-dash.sh to restore enabled
logging after each launch; shell syntax validated. Remote original backed up as
start-turboexo-dash.sh.before-reenable-20261004. No dash restart performed.

Started logging using a temporary always-true start expression, then restored the
above normal trigger. Pi file `2026-10-04_08.29.14.mlg` is open by TSDash, but size
remained 6943 bytes across checks: live telemetry capture is not yet verified.
Key input currently reads 0. Do not treat the open file alone as captured run data.

Restored `--poweroff` on pi-ups-monitor.service locally and on Pi, preserving
-0.20 A threshold and 240 s delay. Service enabled/active and journal confirms
poweroff=True; prior unit backed up as pi-ups-monitor.service.before-reenable-20261004.
At 08:27:31 PDT monitor reported discharge (-0.558 A, 12.364 V), so shutdown is
due around 08:31:31 if external power does not return. No poweroff test performed.
No tune edits or ECU burn performed in this operation.

## 2026-09-28 21:29 — CurrentTune uses exact reference running IAC curve

User explicitly requests the reference90/89/75 curve first, superseding the flat
85% diagnostic. Freshly fetched official Speeduino UA4C99–00 base tune:
https://raw.githubusercontent.com/speeduino/Tunes/main/Mazda/Miata_PNP99-00_SpeedyEFI.msq
**CurrentTune.msq** now has90% at−16.614/19.386°F;89% at42.786,60.786,76.986,
94.986,114.786°F;75% at154.386,188.586,217.386°F. Exact values and temperature
bins checked against reference. Only iacOLPWMVal changed; bins already matched.
Snapshot: `TurboExo_pre_reference_IAC_2026-09-28_212925.msq`.
Open loop,500Hz,Normal,one output and83% crank duty also match reference.
Existing5s crank-to-run taper retained (reference6.2s); this is the exact reference
running curve, not a wholesale reference tune transplant. All other constants
preserved. XML and complete constant comparison passed. Saved only: reload/burn
CurrentTune in TunerStudio; connected-valve result pending.

## 2026-09-28 21:26 — Higher-duty test: CurrentTune running85%

User directs proceeding with higher IAC duty. Snapshotted the latest CurrentTune
to `TurboExo_pre_IAC85_2026-09-28_212632.msq`, then changed all ten running
iacOLPWMVal entries80→85%. **Use CurrentTune.msq.** Retained PWM Open loop,
500Hz, Normal direction, one output, crank83% and5s taper (now83→85 after start).
Only iacOLPWMVal changed; XML/complete constant comparison and backup bytes
verified. Saved only; ECU burn/readback and connected-valve result pending.
The prior80% test excluded a falling ECU command as the stall trigger; its brief
high idle did not establish sufficient physical airflow under all conditions.

## 2026-09-28 19:22 — Unplugged IAC comparison stays running

User explicitly reports IACV unplugged for newest19.20.07 log. Converted/analyzed
`DataLogs/2026-09-28_19.20.07.mlg`; exclude two initial time0 placeholder rows.
Coherent164.556–298.509 s. RPM exceeds400 from169.833 through recording end,
128.676 s, with TPS0 throughout and no captured stall. Ends1434rpm, MAP33kPa,
14.5V, CLT178°F. Late250–298.509 s median1423rpm (1286–1522), MAP33kPa,
14.5V, WUE100–101%. No recorded sync losses or limiter/DFCO activation.

Logged80 is still ECU command only: valve is disconnected. Compared with the
connected80 test, which stopped after about58s, the disconnected test sustains
idle for at least129s and is still running at the end. This strengthens suspicion
of connected IAC valve/drive/airflow behavior; it does not establish the correct
duty, direction, rest aperture or a specific electrical fault. Tests began at
different temperatures (connected~136–138°F vs unplugged149°F), and known manifold
seating/bypass-screw conditions remain uncontrolled. Earlier fixed-duty finding
only excludes a reduction in commanded duty as that stall's trigger; it does not
clear the physical valve or driver. CurrentTune remains the fixed80 diagnostic;
no tune edits made from this unplugged log.

## 2026-09-28 19:19 — Fixed80 applied in log; abrupt stall persists

Newest `DataLogs/2026-09-28_19.17.57.mlg` converted and reviewed. User reports it
died. Latest CurrentTune19:17:56 TunerStudio save has exactly the staged test's
constants. Logged83→80 taper and sustained80 support application of the intended
idle strategy (not a complete ECU readback). No further tune change made.

- Exclude initial out-of-order/placeholder data. Coherent36.963–107.301 s;
  recorded RPM positive39.778–98.082 s, then0 at98.187 s. TPS0 throughout.
- IAC80 from45.316 through97.673 s while firing. During50–95 s, RPM median1244
  (1014–1402), MAP median34kPa, battery median14.5V. Fixed-duty control did not
  achieve a final warm1000rpm calibration; coolant only136–149°F overall.
- Abrupt end:1364rpm at96.300 s →966 at96.791 →699 at96.878 →54 at97.743 →0
  at98.187. Duty remains80 until cranking-state83 at97.809. Battery remains
  14.5/14.4V through initial collapse, then falls. No recorded sync losses,
  errors, DFCO, hard-limit, launch or boost-cut flags. Fan was already on since
  41.051 s; no fan engagement at stall.
- AFR rises toward19.7 during the collapse; this does not distinguish loss of
  fuel delivery from misfire/combustion loss. Commanded PW remains nonzero until
  stopping; physical fuel and spark delivery are unverified. Repeated699rpm and
  MAP36 samples during collapse limit exact event timing/causal interpretation.
- **Verdict:** Reducing commanded IAC duty/closed-loop action is not the trigger
  for this stall. Constant command does not prove constant physical valve flow.
  Asked whether the run was untouched or screw/connector adjustments preceded
  shutdown. Keep80 pending clarification; no evidence-based next duty yet.
  Manifold seating, altered bypass screw and actual oil pressure remain open.
  Oil reads12–13psi during established idle and0 stopped, still unverified.

## 2026-09-28 19:16 — Fixed-80% test applied to CurrentTune

**Use `CurrentTune.msq`**, per the user's explicit instruction. Snapshotted its
latest19:13:34 TunerStudio save immediately before editing to
`TurboExo_pre_CurrentTune_IAC80_2026-09-28_191637.msq`. Applied only
iacAlgorithm="PWM Open loop" and all ten running PWM duty entries80%.
Preserved the newer I=0 and every other constant. CurrentTune now matches the
named diagnostic file byte-for-byte; the earlier instruction to load a separate
file is superseded. XML parsing and complete constant comparison passed.
Saved on disk only: open/reload CurrentTune in TunerStudio, burn, power-cycle and
verify readback. Crank83% → five-second taper → running80%; test result pending.

## 2026-09-28 evening — IAC reconnected; fixed-80% diagnostic staged

**User confirms the IACV had been unplugged during the earlier high-idle testing.**
Plugging it in lowered RPM and the engine then struggled to idle. Earlier logged
IAC64 was ECU command only and cannot establish physical valve response or a
correct minimum duty. User also reports the intake manifold is not fully seated
and the throttle-body idle screw was tampered with; repair/verification remains
unconfirmed. Which screw was moved has not been positively identified on the car.

**Authorized diagnostic file, saved only; NOT confirmed burned:**
`TurboExo_IAC_fixed80_TEST_2026-09-28.msq`. Based on the newer TunerStudio
19:13:34 save of CurrentTune, which has idleKI=0 (the only constant difference
from the 18:11:45 restore point). Changes are PWM Closed+Open loop → PWM Open loop
and all ten running PWM duty values → 80%. Retained crank/pre-start duty83%,
5-second crank-to-run taper, Normal direction, 500 Hz and one output. After the
taper, the requested duty should hold80%; open loop does not seek the1000 rpm
target or use the65–90% closed-loop limits. Idle-up/A/C adders are off/zero.
80% is a diagnostic starting point, not a proven repair or permanent warm-up curve.
Keep IAC connected and hold the mechanical screw setting steady for comparison.
The known manifold seating issue still prevents final idle-air calibration.

Snapshot: `TurboExo_pre_IAC_fixed80_2026-09-28.msq`. CurrentTune was left untouched
to preserve the user's live TunerStudio save. The named test must be opened in
TunerStudio, burned, power-cycled and read back before testing; disk creation
does not apply settings to the ECU. All other constants, including the new I=0,
fuel, ignition, fan and oil settings, were preserved and XML/diffs validated.

Newest log19.09.47: coherent409.202–446.352 s; isolated379.163 s first row excluded.
TPS0 throughout, coolant144–147°F, no recorded sync losses. Initial struggle
439–648 rpm at IAC83–85%; recovery through1000 to1339 rpm as command falls toward
73–76%. User confirms the final1264→822→428→0 sequence was a stall. Command rises
74→80→84 during the collapse; it never reaches the65% floor. These data do not
establish too-low minimum duty or prove the stall is caused by idle-air control.
Logged voltage decline follows RPM decline. AFR/target echo is about75% of firing
samples; no fueling change derived. Oil signal now reaches10–12psi while running
and returns0 stopped, but actual pressure/calibration still needs independent
verification before sustained running. Preceding19.09.10 log is engine-off only.

## 2026-09-28 evening — Newest 18.21.44 log: throttle events captured

Newest local log `DataLogs/2026-09-28_18.21.44.mlg` converted and analyzed.
Coherent recording is 316.771–432.513 s (115.742 s); exclude initial isolated
219.104 s row and 97.667 s gap. Engine runs throughout and ends at1387 rpm/14.5 V;
no stall/shutdown captured and zero recorded sync losses.

- **Idle remains high at minimum command:** stable350–398.581 s median1581 rpm
  (1484–1649) against1000 target, IAC64, MAP32 kPa. Final427–432.513 s median
 1433.5 rpm, still above target at IAC64. CLT reaches162°F, WUE remains102%;
  fully warm equilibrium not established.
- **Four throttle openings:** first to8% TPS gives peak3069 rpm with brief138% AE.
  Second to8% produces a brief1641→1467 rpm dip, then recovers to3490; third and
  fourth reach16% TPS with peaks4303/3815. Second through fourth have AE100%.
  At second tip-in, indicated AFR rises13.4→19.2, MAP28→53 kPa, PW1.758→2.874 ms.
  RPM was already falling after the first release. This captures a hesitation,
  but does not prove lean fueling versus misfire or quantify its cause. No stall.
  Maximum MAP58 kPa: no positive manifold boost recorded.
- **Fan:** commanded on throughout coherent recording, matching physical fan
  confirmation from user. No new switching threshold/hysteresis test.
- **Oil:** coherent data reads0–2 psi (median0), including sustained running.
  The isolated first row's14 psi is not a valid engine-off baseline. Actual
  pressure remains unverified; prior sensor-connection/reference-reading question
  is unanswered. Verify pressure before more sustained commissioning runs.
- **Spartan:** Aux0 again transitions from roughly380 to598; discrepancy with
  nominal0/1/2 V mapping remains. Expected readings, grounding and UA4C JP7/JP8
  configuration are now documented in docs/WIRING.md. No hardware change assumed.

CurrentTune constants still match the18:11:45 restore point; no tune edits or ECU
operations. Idle-air response and oil/status signal verification remain next;
this brief hesitation does not justify an automatic VE/AE change.

## 2026-09-28 evening — 18.17.07 log reviewed; fans physically confirmed

`DataLogs/2026-09-28_18.17.07.mlg` was the newest log at that review; converted to CSV.
About 170 s continuous running, TPS=0 throughout, zero recorded sync losses.
This is a warm-up run (CLT 84–136°F, WUE still 106% at the end), not a fully
warm idle or throttle-bog test. Ignore the initial placeholder row/time gap when
estimating duration. Shutdown follows a sharp logged supply-voltage fall while
RPM is still high; the log does not establish an ordinary idle stall.

- **Idle:** IAC command falls from 89 to 64 by log time 66.306 s, then stays at
  the floor. Firmware integer quantization makes logged 64 consistent with the
  saved 65% minimum at 500 Hz. From 150–214.7 s, target=1000 rpm, median actual
  1555 rpm (1373–1635), MAP median 32 kPa. Controller behavior is consistent with
  the staged closed-loop settings, but physical valve response and complete ECU
  burn/readback remain unverified. Do not increase gains or widen limits from
  this evidence alone; verify IAC response and other idle-air paths first.
- **Fan:** User confirms fans physically work. Fan command turns on at log time
  162.035 s / CLT 120°F, consistent with the user's latest saved threshold.
  Voltage stays around 14.5 V; no stall at fan engagement. Off hysteresis was not
  exercised: fan turns off when the engine stops at 136°F.
- **Oil:** Logged pressure is 14 psi before crank, falls to 0 by 47.430 s, remains
  0 throughout sustained running, and returns to 14 after shutdown. This does
  not validate actual oil pressure. Sensor connection, supply/ground, input and
  calibration/readback need verification and comparison with an independent
  pressure measurement before further sustained running. Oil protection remains
  Off; do not enable it against this unverified signal. Asked user whether sensor
  was connected during this run and whether an independent reading is available.
- **AFR/status:** Late indicated AFR median 12.6 versus target 14.3, with WUE
  still active; no fuel correction derived. Aux0 settles around 598 counts,
  nominally 2.92 V at 5 V/10-bit, still inconsistent with the documented 2 V
  ready output under that direct-input assumption. Readiness and AFR accuracy
  remain separate unresolved checks. No throttle opening/AE event is captured.

**CurrentTune.msq remains the newest combined tune**, all constants rechecked
against the 18:11:45 restore point with no differences. No tune settings changed.
The older named staged files still contain the old fan threshold; do not load them
as the current baseline. Next work is measurement/diagnosis, then discussion of
one controlled idle-air test once actual oil pressure is established.

## 2026-09-28 18:11:45 — Latest combined file is CurrentTune.msq

**Use `CurrentTune.msq` for the latest saved settings.** TunerStudio subsequently
saved it at 18:16:50; all constants still match the 18:11:45 restore point.
The latest log is now analyzed above. The user saved fan-on
120.186°F (displayed 120°F); hysteresis remains 7.2°F. All prior crankRPM 300,
closed-loop IAC and A9 oil-pressure changes are preserved. Compared all constants
with the named 18:06 staged file: only fanSP differs. Restore point:
`restorePoints/TurboExo_2026-09-28_18.11.45.msq` (“User Requested Save of Settings”).
The named `TurboExo_closedloop_oilpressure_2026-09-28_180624.msq` still has 201.186°F
fan-on and is now superseded. Complete ECU burn/readback remains unconfirmed; fan operation is now confirmed
by the user and the latest log, as detailed above. Do not reload the older named copy over the user's newer fan setting.

## 2026-09-28 18:06 — Oil-pressure monitoring staged (superseded by 18:11 save)

**Earlier staged file:** `TurboExo_closedloop_oilpressure_2026-09-28_180624.msq` (matched CurrentTune at 18:06), saved only; not confirmed
burned. Includes the crankRPM300 and closed-loop IAC setup below. A9 / UA4C INP2
now supplies native oil-pressure monitoring. User sensor:0.5–4.5V=0–100psi.
Saved calibration at0V/5V is -13/113psi (whole-psi approximation of -12.5/112.5).
Automatic oil-pressure protection stays Off pending verified readings. Snapshot:
`TurboExo_pre_oilpressure_2026-09-28_180624.msq`. Burn, power-cycle and verify readback; check engine-off pressure near
zero and compare running pressure against a reference before enabling protection.
INP1/A8 remains Spartan status. No other constants changed in this oil-pressure edit.

## 2026-09-28 — Sustained running; warm idle tuning; closed-loop tune staged

**Current ignition hardware:** four Toyota/Denso **673-1300 / 90919-02239 COPs**,
confirmed again by the user 2026-09-28. Original Miata coil packs/plug leads have
been replaced. Documented wiring: IGN1→1, IGN2→3, IGN3→4, IGN4→2. Saved ignition
mode is **Wasted COP**; earlier Sequential and stock-coil sections below are historical.

**Current phase: idle and running calibration.** This supersedes the no-start
front line below. The 13.09.03 log contains ~328 s continuous running and ~233 s
uninterrupted closed-throttle idle. The 13.29.24 log contains ~16.9 s coherent
warm idle: CLT 187–190°F, WUE 100%, median RPM 1601, MAP 32 kPa, AFR 12.1 versus
14.3 target, IAC 75%. No recorded sync losses. Latest warm log has TPS=0 throughout;
it does not capture the reported throttle bog. Earlier blips bogged with AE active;
lean-indicating spikes do not distinguish lean mixture from misfire. User reports
flutter only after releasing throttle following the bog; a bypass is installed.
No positive manifold boost was recorded; pre-throttle pressure is not measured.

**Saved, NOT confirmed burned:** `CurrentTune.msq` and `TurboExo_closedloop_2026-09-28_142246.msq` now set crankRPM
300 (was 800), PWM Closed+Open loop, duty limits 65–90%, P=0.0625, I=0.03125, D=0,
TPS integral-reset threshold 2%, RPM reset hysteresis 1000 rpm. Targets taper from
1200 cold to 1000 rpm at 114.8°F and above. The existing open-loop duty curve remains
the feedforward baseline; PWM frequency 500 Hz, Normal direction, crank duty 83%,
fuel and ignition settings are unchanged (stock reds, reqFuel 12.7, Semi-Sequential,
Wasted COP, running dwell 2.5 ms). Baseline: `TurboExo_pre_closedloop_2026-09-28_142246.msq`.

**Earlier proposed test (superseded by the evening findings above):** Use the latest
CurrentTune.msq, never the superseded named staged files, and power-cycle the ECU
(the INI marks duty limits as requiring it), then verify readback. Log a warm idle
and gentle throttle return. These are provisional controller settings, not a proven
valve calibration: if duty reaches 65% while idle remains high, do not assume target
was achieved or automatically widen the limits. Check valve response and other air
paths. Combined mode can briefly approach the 90% ceiling after cranking because
of integral initialization; it does not use the old PWM open-loop taper.

**Wideband replacement confirmed by user, 2026-09-28:** The OEM module was replaced
with the non-OEM Spartan that has the status wire. Use the downloaded manufacturer
manuals in `docs/manuals/`, not the OEM pinout. Spartan 3 v2 page 1: brown output
0 V waiting / 1 V heating / 2 V heat-up complete. Warm Aux0 565–604 counts nominally
converts to 2.76–2.95 V at 5 V ADC reference, so status decoding still requires
verification of the input transfer or brown-wire voltage/firmware. Readiness is
separate from AFR calibration. Earlier model-conflict/LED interpretations are
superseded; exact replacement revision has not been read back.

## 2026-09-25 evening: fuel to all four cylinders for the first time; catches but no run

**Front line.** Paired injection on this individually wired harness drove INJ1 and
INJ2 only (firmware `init.cpp`, INJ_PAIRED: schedule 1 → injector 1, schedule 2 →
injector 2). Cylinders 3 and 4 had never been fueled; the July idle ran on two
cylinders. `injLayout` is now **Semi-Sequential** (1+4 & 2+3), burned 18:04, and all
four plugs came out wet afterward. `crankRPM` is **300** (raised from 250 at 16:34).
Logged `PW3`/`PW4` are 0 by design in Semi-Sequential.

Engine still catches repeatedly (up to 21 catches per crank session, peaks 647–710
rpm) and crawls at 500–700 rpm under 30–80% throttle with MAP at 98 kPa, then dies.
Crank-lock catches prove cam phase and the IGN→cylinder map are right (the tooth
only ends a coil charge already running on its sequential schedule). Fuel tables
match the July known-good. The one system changed for the worse since July is
ignition: dwell 6.0/3.0 ms on two wasted-spark coils → 4.0/2.5 ms on four Denso COPs.

### Immediate next actions

1. `crankRPM` 300 → 800, burn, one crank ≤5 s, throttle steady under 60%, no
   blips, log. Climbs through 800 → run-mode ignition path is the fault; then
   restore crankRPM and raise `dwellrun` to 4.0 to split dwell from timing.
   Still crawls → raise `dwellcrank`/`dwellrun` together (coils unverified in
   both regimes).
2. Record plug condition after each crank. Do not tune fuel from logged AFR.
3. Cranks ≤5 s. The 18.16 log had a 34 s crank; that fouls plugs and heats the starter.

Full reasoning and evidence: `EXPERIMENT_LOG.md`, 2026-09-25 (PM) entry.

## 2026-09-25 morning: COP complete; diagnose crank/no-start (superseded by the evening section)

**This section supersedes the older state below, including its logging and spark
claims.** The engine previously sustained a cold idle; today's issue is no-start
after the completed Toyota/Denso 673-1300 / 90919-02239 COP conversion.

- Sequential ignition: **IGN1 → cylinder 1, IGN2 → 3, IGN3 → 4, IGN4 → 2**.
  Cylinder 1 is at the timing-belt end. The user confirmed strong spark on all
  four coils in hardware output testing. Actual spark and timing during cranking
  remain unverified after conversion.
- Stock 238 cc red injectors: harness is **individually wired** (INJ1–4 → cyl 1–4);
  the tune said Paired until 18:04 (see evening section). Bench testing and
  cleaning completed. A new battery was installed between today's first and
  second logs.
- Saved `CurrentTune.msq`: reqFuel **12.7 ms**, injector opening **1.0 ms**,
  restored VE baseline, prime pulses 30/30/25/25 ms, protection maximum 4000 rpm,
  crank threshold **250 rpm**, flood clear 60% TPS. Ignition: **Sequential**,
  **Going Low**, crank timing lock **On**, dwell **4.0/2.5 ms** crank/run, dwell
  map No, overdwell protection On/10 ms, dwell error correction Off. Miata 99–05
  trigger, trigger angle 0°, rising edges, cranking advance setting 10°.
  Saved settings do not independently prove every burned ECU setting.
- Keep **Fix cranking timing with trigger On**, per the
  [official Miata decoder guide](https://wiki.speeduino.com/en/decoders/Miata_99).
  Earlier advice to turn it Off was retracted. Extended scheduled dwell does not
  prove equivalent physical coil charging time. The 4.0/2.5 ms values are
  provisional starting recommendations, not published Denso specifications.
- An older controller tune briefly overwrote the file with reqFuel 6.9 and other
  stale settings. The baseline was restored before COP changes were applied.
  Recovery baseline: `restorePoints/TurboExo_2026-08-29_19.22.11.msq` (pre-COP).
  The September 25 **10:28:35** restore point contains the stale tune.

### Latest evidence

Local `DataLogs/` contains `.mlg` originals and semicolon `.csv` conversions.

| Log, 2026-09-25 | Recorder | Cranking result | Commanded dwell / Gbaro |
|---|---|---|---|
| `10.44.47` | Pi, old battery | ~9.5 s captured, peak 223 rpm; mostly 8.9–9.3 V | ~4.2 ms / 100% |
| `13.16.22` | Pi, new battery | Two cranks ~6.5/7.6 s, peak 251 rpm; mostly 10.3–10.6 V | Both logged zero; inconsistent with other data |
| `14.33.35` | Desktop, new battery | Two cranks ~5.3/3.5 s, peak 253 rpm; mostly 10.5–10.6 V | Mostly 4.12 ms / 100% |

All crank sections have full sync and zero recorded sync losses; none shows a
clear catch. Barometric **pressure is 99 kPa**, including the log whose **Gbaro
fuel correction** is zero. That zero conflicts with the saved all-100% table and
substantial fuel commands. Desktop logging did not reproduce the zeros. A data
path problem is suspected; the precise cause remains unproven.

The desktop log commands matching PW1/PW2, generally 15–16 ms, with no flood-clear
cuts. Cranking MAP is 90–98 kPa, IAT 59°F and coolant 84–86°F. Its measured-dwell
field reaches ~16.5 ms; firmware measures scheduler elapsed time, which need not
equal pin on-time with crank lock. Do not diagnose overcharging from that alone.
Timestamps reset near the end and the first two are out of order; analyze coherent
crank sections at 74.678–79.937 and 93.561–97.076 seconds. The analyzer's negative
total duration is invalid.

### Immediate next actions

1. With injectors disabled, verify physical spark during a brief actual crank,
   then timing near 10° BTDC. All four hardware output tests already passed.
2. Confirm live settings against the saved baseline. Do not retune fuel from the
   Pi's inconsistent channels or the short-crank AFR readings.
3. Confirm recording before each attempt; prefer a desktop log for comparison.
   Keep cranks short and record plug condition when needed.
4. Revisit hot-idle air only after it starts. The July hot-stall finding does not
   establish the cause of today's no-start.

### Logging and wideband status

Pi: `dietpi@192.168.1.134`; TSDash API at `http://192.168.1.134:16680`.
Project: `/home/dietpi/TSDashProjects/TurboExo_2026-06-01_21.16.20`.
**Automatic logging was disabled when checked live today.** Both Pi logs were
started/stopped manually and downloaded with matching SHA-256 checksums. No Pi
log was open at the last check. The newest attempt was logged locally. Older
August automation notes below do not describe today's logging state.

Aux0 is Analog_local on A8 / UA4C INP1 for wideband status. The user renamed it
WideBandStatus, but some files/logs still use Aux0. Levels near 93/402/604 counts
need controller-model/output verification before assigning readiness meanings.
Spartan model remains unresolved. AFR/target equality is ECU echo behavior;
echo presence or absence alone does not establish sensor validity. Today's
short attempts provide no reliable AFR mixture diagnosis.

Use `/opt/homebrew/bin/python3.12` for analysis while system Python is blocked by
the Xcode license prompt. `analyze_log.py` contains yellow-injector dead-time
assumptions; do not apply those estimates to the currently installed stock reds.

## Historical context (through August 30)

_Update whenever the loaded tune or the front line changes. Full history:
`EXPERIMENT_LOG.md`. Pinned facts: `docs/REFERENCE.md` (every line provenance-tagged)._

> **2026-07-25 — it idles cold and stalls hot, and the cause is measured.** Nine logs this
> morning. The engine held a closed-throttle idle for **250 s** at 800–1000 rpm in
> `2026-07-25_09.17.01` while coolant was 82–127 °F, then stalled at closed throttle in every
> later log once coolant passed ~155 °F. `iacAlgorithm` is **PWM Open loop** — coolant lookup
> only, zero RPM feedback — and `iacOLPWMVal` drops **89 % → 75 % between the 114.8 °F and
> 154.4 °F bins**. Sorted by coolant at death: 127 °F/89-85 % → idled 250 s; 131/84 → 0.6 s;
> 156/75 → none; 165/75 → 1.5 s; 171/75 → 0.7 s. Within 09.17.01 the duty stepping 89→85
> tracked idle down 940→800 rpm, ~30 rpm per duty point — so **the valve flows and responds;
> the commanded hot duty is just too low.** ("IACV not flowing air" is retracted.)

## Historical loaded tune (2026-07-19, verified live 2026-07-25)
`CurrentTune.msq` = **OEM stock injectors** + factory fuel baseline: reqFuel **12.7**,
`injOpen` **1.0**, `battVCorMode` **Whole PW**, `crankingEnrichTaper` **5.0 s**,
`primePulse` 30/30/25/25 ms, `CrankAng` 10°, `engineProtectMaxRPM` **4000**, `crankRPM` 230,
`tpsflood` **60**, factory-transplant VE.
Back-solving PW from `2026-07-25_09.33.18` gives reqFuel 12.73 — **the file matches what's
burned.** Snapshot: `restorePoints/TurboExo_2026-07-19_12.23.39.msq`.

## Pi logging / USB backup (2026-08-30)
The Python UPS monitor now publishes valid connected/discharging transitions to
a one-line software GPIO. TSDash's saved configuration maps logical GPIO17 to the
active-high `AppEvent.ignitionOn` input; the bridge redirects only that pin, and live
LOW/HIGH reads plus callbacks passed while physical RP1 GPIO17 stayed untouched.
Invalid I2C samples retain the last published value. UPS/J2 wiring is unchanged.

The first physical crank proved the RPM start, but exposed a startup race: the
virtual line's former low default pre-qualified stop before logging began, causing
an immediate stop/restart and leaving a header-only file open. The line now defaults
high; start requires RPM plus ignition high, and stop requires a log older than five
seconds plus two seconds of ignition low. A clean-session regression log remained
open after start and closed on virtual key-off without restarting TSDash.

The next physical power-loss test passed: Python drove the software GPIO low and
the Pi completed its existing four-minute shutdown. No `.mlg` was expected because
that test had no RPM event. The one remaining acceptance test is a solid crank
followed by key-off in the same session, proving start, native close, conversion,
and USB hash together.

## Historical hot-idle follow-up (resume after the current no-start is resolved)
1. **Raise hot idle air.** `iacOLPWMVal` rows at 154.4 / 188.6 / 217.4 °F from 75 → ~88–90,
   and add a bin between 114.8 and 154.4 so it ramps instead of cliffing. Burn, warm it up
   past 170 °F, close the throttle. This is the one change — don't stack others with it.
2. **Then close the loop.** If it holds hot, switch `iacAlgorithm` to Closed Loop PWM
   (target ~850) so it stops depending on a hand-fitted temp curve.
3. **Idle ignition stabilization.** `idleAdvEnabled` is Off, so advance *retards* 19→16° as
   RPM sags — the opposite of what catches a stall. Enable with ±5° once idle air is sorted.
4. **Alternator, settled properly.** Every recent run was jumped from an idling donor, so
   13.3–13.5 V proves nothing. Disconnect the jumper while running: holds ~13.5 = charging,
   decays toward 12 = not.
5. **Plug read after a sustained run** — still the only mixture signal, and the #2 re-test.
6. **Warm-idle vacuum check** once it idles: MAP should sit 28–37 kPa; > ~40–45 warm means
   a leak in the new turbo plumbing.

## Open questions (do not guess — see `docs/REFERENCE.md`)
- **AFR is unusable.** Pegged at exactly 19.700 from t = 24.8 s onward in 09.33.18, through
  large MAP and throttle swings. Not a mixture reading. No usable AFR from any run yet.
- **Spartan 2 or Spartan 3?** Notes contradict each other; nobody has looked at the box.
- **Does #2 fire?** Only #1 was ever strobed. No swap test was run.
- **What was the 2026-06-20 trigger wiring fault?** Never recorded.

## Historical checks with the old ignition
Trigger / full sync (status 2, 0 sync loss all morning). Base timing (timing light, within 1°).
MAP plumbing and sensor (moves 39–100 kPa). Fuel config (factory 12.7 baseline, verified live).
`IgInv` "Going Low". The IACV itself.
