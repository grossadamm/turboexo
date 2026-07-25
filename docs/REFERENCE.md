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
- Vehicle: 1999 Mazda Miata NB1, 1.8 L BP-4W, 1839 cc, 4-cyl, firing order **1-3-4-2**. `[user]`
- Forced induction: external **TD04L-13T** turbo. The build was rewire + turbo only; internals known-good (engine ran before the build). `[user]`
- ECU: **Speeduino UA4C, firmware 202501**. Speed-density, wasted spark, paired injection (`injLayout` = Paired, `inj4CylPairing` = "1+4 & 2+3"). `[tune]`
- **No factory instrument cluster.** The dash is TunerStudio on a Raspberry Pi, reading everything over the serial link — so tach-output settings (`tachoDuration`/`tachoMode`/`tachoDiv`) are irrelevant. `[user 2026-06-12]`
- Link: `/dev/cu.usbmodem101` @ 115200. A **data** USB cable is required — charge-only cables enumerate nothing. `[user]`
- Log tooling: `npx mlg-converter --format=csv <file>.mlg` → semicolon CSV in `DataLogs/`. `[user]`
- Hidden TS Hardware Test page: enable via `projectCfg/project.properties` (`enablehardware_test`). `[user]`

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
- ⚠️ **Model unresolved.** Notes have variously recorded Spartan 2 (user-confirmed 2026-06-28) and Spartan 3. Nobody has re-checked the box. Resolve by looking at it before relying on any model-specific warmup behavior.
- Cal is linear **0 V = 10.0 AFR, 5 V = 20.0 AFR**; sensor is LSU 4.9. `[tune + user]`
- Warmup output sequencer emits fixed cal voltages before the sensor is valid: ≈1.66 V = **13.3 AFR**, second plateau ≈3.33 V = **16.7** — the source of the pinned 13.1–13.2 / 16.4–16.5 in crank logs. `[web: 14point7]`
- **AFR echo:** `readO2()` always logs the raw sensor as AFR; `calculateAfrTarget()` returns live O2 as *Target* while `runSecs <= ego_sdelay`, and `runSecs` resets every crank. So on short catches Target shadows AFR and the pair is not mixture data. `[src: Speeduino 202501 sensors.cpp / corrections.cpp]`
- `egoType` Wide Band, `egoAlgorithm` No correction, `ego_sdelay` 15 s, `egoRPM` 1200, `egoTemp` 185 °F. `[tune]`
- **2026-07-25: AFR pegged at exactly 19.700 from t = 24.8 s to the end of the run, through big MAP and throttle swings** (and from t ≈ 51 s in 09.17.01). A pegged rail is a sensor/wiring fault or an un-heated sensor, not a mixture reading. There is still **no usable AFR data from any run.** Read plugs. `[log]`

## Knock
- The UA4C analog knock input has a **raw piezo sensor wired straight to it** — Speeduino needs a conditioned 0–5 V signal (TPIC8101 module or Phormula KS-4; band-pass ≈ 6.9 kHz for the 83 mm bore). `[user 2026-06-09 + web]`
- `knock_mode` = **Off**. `[tune]` Leave it off until a conditioner is fitted and the threshold calibrated at clean WOT.

## Ignition
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
1. **Is the alternator charging?** Recent runs were jumped from an idling donor car, so the 13.3–13.5 V running voltage is the donor's and proves nothing either way. Test: disconnect the jumper while running — holds ~13.5 = charging, decays toward 12 = not. `[log shows the voltage; the cause is unknown]`
2. **Spartan 2 or Spartan 3?** See Wideband.
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
