# ESP32-P4 cluster implementation plan

Status: implementation integrated; initial cross-build matrix and native host checks pass. Preparing nine-agent Change review; final rebased gate and branch push remain. User authorized
planning, independent review, delegated implementation, nine-agent Change
review, remediation, validation and branch push without a plan-approval stop.

## Outcome and boundaries

Implement native firmware for the purchased **4D Systems ESP32-P4-70**, a
1280×800 non-touch cluster, using the accepted Street/Track/Tuning designs in
`dashboard/esp32p4-mocks/`. The deliverable is a reproducible ESP-IDF build,
portable host-tested telemetry/application logic, an actual LVGL desktop render
of the same UI code, and documented board/ECU commissioning gates.

This change does not flash the P4, change/burn any ECU settings, replace the Pi,
merge to main, deploy, or claim physical frame-rate/startup/vehicle validation.
Hardware verification is a separate execution boundary, not a reason to leave
repository work unfinished. Existing tune/log/dashboard artifacts are preserved.
The accepted HTML mocks remain the design authority and are not redesigned.

The user specified the workflow in the **calendar_automation** repository:
`docs/delegated-execution.md`, `docs/software-factory.md`, and its AGENTS.md
completion/delegation rules. Follow the nine independent review perspectives.
The existing isolated task branch is retained for this continuing task. Keep
all toolchains/dependency clones in persistent `TurboExo-deps/` beside the primary
checkout; no dependency installs in temporary directories. The imported
calendar-specific pnpm/Compose/TypeScript gates do not apply to this new C++
project; provide equivalent reproducible firmware/host/documentation checks in
`scripts/verify-firmware.sh`. Plan approval is explicitly already authorized.

## Evidence and decisions

- Board evidence: `research/board.md`. Pin ESP-IDF v5.5.5, vendor LCD component
  0.1.1, LVGL 9.5.0, esp_lvgl_port 2.7.0; preserve resolved dependency locks.
  Panel scans 800×1280; native UI is landscape 1280×800 via 90°/270° rotation.
  Produce pre-v3 and v3 SoC profiles; do not guess the delivered chip revision.
  Pin pre-v3 `CONFIG_ESP32P4_REV_MIN_0=y`; v3 uses
  `CONFIG_ESP32P4_REV_MIN_300=y` (the SDK otherwise defaults to 3.1).
- Protocol evidence: `research/protocol.md`. Speeduino 202501/.6/.7 secondary
  Serial3 Generic(ini) 115200 8N1, raw `S` identity and fixed `r` reads only.
  Exact complete version matching uses a quiet-gap deadline, not prefix match.
  Two fixed read spans (0–43 and 76–108) fit the nominal AVR TX buffer. No
  pipelining; publish only a completed bounded two-span cycle. Start at 5 Hz.
- Separate ESP UART1 on proposed GPIO17 TX / 18 RX; debug uses USB Serial/JTAG.
  Level translation and board revision must be verified before connection.
  Never send boot logs, arbitrary console strings or ECU-write commands there.
- Optional external ADS1115 on GPIO15 SDA / 16 SCL supplies fuel and oil
  temperature after calibrated conversion. Local main contains newer sender
  evidence, but those unrelated unpublished commits are not merged into this
  branch. The current working circuit/calibration remains a bench dependency.
- Default firmware source is explicit **replay**, with visible REPLAY indication;
  live UART is opt-in via build configuration. In live mode, no simulated values
  enter the model. The replay preserves the accepted actual/simulated provenance.
- Physical controls on GPIO19/20/21: cycle Street/Track/Tuning, cycle brightness,
  pause/resume replay (no effect on ECU). Debounce and held-button behavior are
  deterministic. Persist mode and brightness only after changes settle.
- No wireless, remote commands, tuning editor, OTA, or ECU actuation is added.

## Architecture and interfaces

`firmware/cluster/` owns ESP-IDF project configuration, platform adapters,
portable core, shared LVGL UI, host harness, assets, tools and tests.

### Portable core (no ESP or LVGL dependency)

- Fixed-size typed telemetry model: metric value, source/quality, monotonic
  observation timestamp. Metrics cover accepted displays (RPM, speed mph,
  oil psi, coolant °F, fuel %, oil temp °F, absolute MAP kPa, signed boost psi,
  TPS %, raw AFR, reported target, advance degrees, PW ms, duty %, IAT °F,
  battery V and diagnostic correction/status fields where verified).
- Poller state machine: startup drain/quiet, bounded exact identity, two
  sequential fixed span reads, deadlines, malformed/extra-byte rejection,
  recovery backoff. Require a quiet guard after each exact 46/35-byte reply,
  before the second request and before publication; extra bytes invalidate both
  spans. Output transactions come only from compiled read commands.
  A UART write failure/partial request latches a transport fault instead of
  blindly resending into the ECU's incomplete command parser. A P4 restart is
  not an ECU parser reset. Every live boot starts disarmed in AwaitEcuReset.
  The screen requests an actual ECU reset followed by holding Mode to confirm;
  only that explicit confirmation enables initial communication or clears an
  uncertain-TX fault. There is no automatic reconnect after a P4 reboot and no
  NUL-padding recovery: source review found a byte-framing brownout counterexample.
- Decode explicitly typed little-endian/signed fields and derived units; keep
  transport integrity limitations visible (legacy protocol has no CRC). Reject
  structurally invalid packets. Per-sensor plausibility invalidates only that
  metric, never erases ECU protection flags or unrelated data. Do not treat
  plausible data as electrically verified. A cycle is not an atomic ECU snapshot.
- Per-metric freshness, link state and sensor qualification remain separate.
  Default freshness is 1000 ms for the 5 Hz ECU cycle. Stop/crank/sync loss
  (including changed loss counter)/reconnect reset the conservative target gate.
  Require continuous fresh synchronized running for ego_delay + 1000 ms (default
  16 seconds); ECU uptime byte is not runSecs and its 255→0 wrap is normal.
  Live Tuning exposes AFR only as explicitly diagnostic RAW AFR/UNVERIFIED while
  readiness is unknown; the target is unavailable during its echo-risk window.
  Replay retains raw values with its visible source indication. No guessed
  Aux0 readiness threshold or inference from AFR/target equality.
  VSS and calibrated oil are enabled explicitly for live display; absent sources
  are distinct from measured zero. Fuel/oil temperature require calibration.
- Bounded eight-second history with gaps on stale/missing data; no interpolation
  over disconnects. RPM animation may interpolate; displayed values remain
  measured. Clamp graphical range, not recorded numeric measurements.
- Pure input debounce, mode/brightness state, monotonic replay and calibration
  interpolation are host-testable. Calibration knots must be finite, ordered
  and bounded; invalid profiles never produce plausible engineering values.

### Native UI (shared desktop and ESP)

- Render all three accepted modes with LVGL, not an HTML/webview approximation.
  Reuse positions/colors/scale meanings, retain the large centered Street
  speed/tach, Track orange ribbon + complete four bars, and Tuning traces.
- Keep labels/scales/icons legible and clear of readings at extreme values.
  Retain recorded-vs-simulated indication in replay and explicit stale/offline,
  warming/unqualified and ECU-protection states in live mode. ECU protection
  flags are information only; firmware does not command protections.
- Static objects/drawing geometry and bounded update work; no object recreation
  per frame. Use bundled licensed fonts/icons, deterministic layout constants,
  and no network asset dependencies. UI never owns UART or file operations.
- Provide desktop interactive controls and offscreen screenshot fixtures from
  the same LVGL renderer at 1280×800. Inspect accepted/replay, disconnect,
  warmup/unqualified, overrange and ECU-warning states across affected modes.

### ESP platform

- Initialize manufacturer panel, LVGL rotation, PSRAM buffers and backlight.
  UART parsing, sensor IO, SD writes and display work have bounded independent
  task responsibilities and synchronized snapshots, not shared mutable races.
- UART task drives the portable state machine. Non-touch buttons and NVS
  preferences work without a laptop. Logging/debug uses the USB console only.
- ADS1115 adapter: optional disabled-by-default I²C, bounded read timeouts,
  piecewise calibrated fuel/oil-temperature conversion; missing/invalid
  calibration or bus failures invalidate just those metrics.
- Optional SD CSV logging of timestamped values/quality with a bounded queue,
  unique per-boot filenames, periodic flush and explicit failure/drop status.
  Never format a card automatically; card absence/failure cannot block gauges.
  UI and serial start before optional card mounting. No claim of guaranteed
  power-loss durability; no fabricated wall-clock dates without an RTC source.
- Watchdog-aware task loops, allocation/init failures handled visibly where
  display remains usable; GPIO collision checks and configuration validation.

## Ordered work and acceptance checks

- [x] Finish board/protocol/setup research with pinned official sources and
  verified/open distinctions; identify the imported workflow source.
- [x] Independently review this plan, resolve confirmed findings, commit the
  plan/research checkpoint, then proceed without another approval checkpoint.
- [x] Define shared C++ core/UI/platform interfaces before parallel writers.
  Contract: `INTERFACES.md` and `include/cluster/types.hpp`; core, UI and
  platform implementation owners are now working in non-overlapping paths.
- [x] Implement/test the protocol and model with known-byte fixtures for
  endian/scaling/signedness, identity suffixes, partial/noisy/extra responses,
  timeouts, recovery, truncated writes, stale data and startup validity gates.
- [x] Implement/test replay, 8-second bounded history, calibration and buttons;
  fixtures detect source mixing, stale curves, time-wrap and repeated presses.
- [x] Implement native Street/Track/Tuning and desktop fixture capture; inspect
  actual LVGL images against accepted HTML snapshots, correct visual defects.
  Compare all three explicit modes at replay offsets 20 s and 31.705 s (peak),
  plus live disconnected, target-warmup/raw-unverified, ECU-oil-protection, and
  extreme values. Render 1280×800 PNGs under a persistent artifacts path.
  Native default is Street; saved mode takes precedence. The accepted replay
  HTML defaults to Track via its build wrapper; source player defaults alone
  do not define native behavior.
- [x] Implement the board adapter, persistent controls, optional calibrated
  sensors and SD logging; tests exercise pure failure handling where hardware
  access is unavailable, and cross-build all configured platform paths.
- [x] Integrate and build isolated replay/live × pre-v3/v3 configurations, each
  with its own sdkconfig and build directory; assert generated revision minimums.
  Compile optional ADS and SD branches in checked live profiles. Capture binary
  size and pinned dependency versions. The isolated 5.5.5 toolchain was repaired
  and its generic P4 probe now passes; target board profiles still need builds.
- [x] Document build commands, pin maps, UART setup/Aux-mode caveat, calibrated
  input enablement, logging, controls, provenance and physical acceptance gates.
- [ ] Run nine read-only Change reviewers in bounded batches against one commit
  range/diff and the same UI captures: Cleanliness (Luna), Completeness (Terra),
  Bugs (Sol), Scope (Terra), Holistic integration (Sol), Legacy/fallback/dead code
  (Luna), Documentation (Luna), Whiplash/regressions (Sol), Constants/config
  (Terra). Main validates/deduplicates findings and fixes confirmed in-scope
  issues; recheck affected contracts rather than restarting review needlessly.
- [ ] Retire this completed plan per imported lifecycle; retain durable
  decisions/procedures and hardware gates in firmware README/research docs.
- [ ] Commit, fetch and rebase onto current origin/main (or branch upstream if
  already published); run final relevant local gate on rebased commit; push
  this task branch, fetch and confirm HEAD equals its remote. Do not merge.

## Validation evidence and remaining gates

Research: official vendor driver/schematic and Speeduino source are being
verified by separate agents. Setup: IDF5.4.3 P4 probe succeeds but is below vendor
minimum; isolated pinned5.5.5 toolchain setup is underway in persistent storage.

Physical gates (document, do not execute in this change): delivered board/SoC
revision, upright landscape rotation and color, boot time/frame pacing/tearing,
voltage-level/pin verification, physical buttons, primary USB + Serial3
coexistence under ECU load, Aux0 mode after secondary serial is enabled,
VSS calibration and ADS sender curves, actual SD power-loss behavior.

## Independent plan review resolution

Sol review identified per-response quiet guards, partial-TX/reset distinction,
independent sensor qualification, delay+1-second target gating, explicit silicon
minimums and isolated build/UI fixture matrices. Those requirements are now
incorporated above. The partial-command startup recovery proof found an unsafe brownout case;
explicit operator-confirmed ECU-reset gating resolves it without per-request
flash writes. The isolated toolchain reinstall resolved the binutils failure and its generic
P4 build passed; real platform profiles still require cross-build evidence. No additional approval checkpoint is required.

## Integration evidence

All four replay/live × pre-v3/v3 profiles compiled on the pinned SDK;
revision minimums and live/replay symbol separation were verified. Host core
checks pass under ASan/UBSan. The same LVGL renderer exports 30 fixtures covering
all modes at the two replay offsets and offline, warmup, protection, extreme,
peripheral and logging states. Integration corrected Tuning RPM wrapping,
replay-pause timestamp handling, compact inline units, and an extreme-speed
label collision. Final native RPM graphics use a tested 80 ms display-only
transition while numeric values/history remain recorded. The final gate will
rebuild the current reviewed source after rebase.
