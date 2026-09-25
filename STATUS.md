# TurboExo — Status (living)

## 2026-09-25: COP complete; diagnose crank/no-start

**This section supersedes the older state below, including its logging and spark
claims.** The engine previously sustained a cold idle; today's issue is no-start
after the completed Toyota/Denso 673-1300 / 90919-02239 COP conversion.

- Sequential ignition: **IGN1 → cylinder 1, IGN2 → 3, IGN3 → 4, IGN4 → 2**.
  Cylinder 1 is at the timing-belt end. The user confirmed strong spark on all
  four coils in hardware output testing. Actual spark and timing during cranking
  remain unverified after conversion.
- Stock 238 cc red injectors remain **paired**; the user reports bench testing
  and cleaning completed. A new battery was installed between today's first and
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
