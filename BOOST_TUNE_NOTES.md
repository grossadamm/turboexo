# TurboExo — Tune Notes (NA→Boost Extension + Commissioning Settings)

**Car:** 1999 Mazda Miata, 1.8L BP, turbocharged (Exocet-style build), TD03L-13T @ ~7 psi spring
**ECU:** UA4C Speeduino, firmware `Speeduino 2025.01.7`
**Fuel system:** RX-8 "yellow top" injectors (~425 cc/min @ 43.5 psi), **fixed 3-bar** regulator (NOT boost-referenced), pump 91 AKI
**Boost plan:** target ~150 kPa abs (~7 psi), fuel/spark cut (`boostLimit`) at 160 kPa
**Built:** 2026-06-08/09 · **Last updated:** 2026-06-12 (first-start fixes, §7.3)
**Tune to load for first start:** `TurboExo_FirstStart.msq` (see §9)

This file is the **single source of truth for every setting value**. The garage
procedure lives in `FIRST_START_CHECKLIST.md` and points back here for values.
The two scripts' docstrings are canonical for their own behavior (§9).

> ⚠️ **SAFETY:** Everything below produces **STARTING maps to be verified on a wideband + knock detection**, brought up incrementally. They are not "load and floor it" maps. Boost fueling/timing errors cause lean detonation and destroy engines.

> ⚠️ **The NA base is unproven.** The car has never run since the rewire/UA4C/turbo
> conversion. The *entire* VE and spark tables are estimates until road-tuned on the
> wideband (checklist Phase 6 is a full from-scratch NA tune). The boost rows are
> placeholders extrapolated from that unverified anchor — regenerate them (§9 pipeline)
> after NA tuning. The original NA estimate is preserved at
> `restorePoints/TurboExo_2026-06-12_13.21.07.msq`.

---

## 1. The problem

The NA tune's fuel (`veTable`) and spark (`advTable1`) load axes **stopped at 100 kPa** — zero coverage above atmospheric. Above 100 kPa the ECU clamps the top row, so under boost it would run **lean fuel + too much timing → detonation**. There was no active 2nd table (`fuel2Mode`/`spark2Mode`/`stagingEnabled` all Off).

Speeduino tables are a **fixed 16×16 grid** — you cannot *add* rows. The load axis had to be **respread** (redistributed) to cover boost, which costs some low-load resolution.

---

## 2. Key facts extracted from the source tune

| Setting | Value | Why it matters |
|---|---|---|
| `algorithm` | MAP (speed-density) | fuel = f(MAP, RPM) |
| `multiplyMAP` | **Off** → changed to **Baro** | see §3 |
| `incorporateAFR` / `includeAFR` | **No** / No | AFR table does NOT affect open-loop fuel — richening must live in VE |
| `reqFuel` | 6.9 ms | matches 425cc injectors (see §4) |
| `injOpen` (deadtime) | 0.9 ms | |
| `divider` / `injLayout` | 2 / Paired | injector fires once per crank rev |
| `stoich` | 14.7 | |
| `useExtBaro` / `baroPin` | **Yes** / A7 | UA4C has a dedicated atmospheric baro sensor → Baro mode is safe |
| `baroCorr` | Off | separate optional correction curve; left off |
| `boostLimit` | 160 kPa | hard fuel/spark cut |

---

## 3. The fueling math (verified against Speeduino docs)

Speeduino pulsewidth:

```
PW = (MAP/baro) × (stoichAFR/targetAFR) × (VE/100) × reqFuel + deadtime
```

- With `multiplyMAP=Off` the `MAP/baro` term = 1.
- With `incorporateAFR=No` the AFR term = 1.

So the **original** tune was literally `PW = (VE/100) × reqFuel + deadtime`. That means:
1. The VE table was **not** true VE — it was a hand-built fuel-vs-load map (numbers rise from ~40 at idle to ~95 at WOT *because* the tuner baked the load scaling in).
2. Boost fuel had to be **multiplied into the VE numbers**, and because the AFR table is inert, **richening also had to go into VE**.

### Why `multiplyMAP = Baro` (the chosen setup)

Turning the MAP term on makes fuel scale with manifold pressure automatically, so the VE table becomes **true VE** (a flat ~75–110% surface) and:
- **Never overflows the 255 VE-cell cap** under boost (with it Off, cells overflow ~2.7 bar).
- Is physically meaningful and autotune-friendly.
- `Baro` (vs `100`) normalizes to the **live A7 baro reading**, giving automatic altitude/weather compensation. Firmware tooltip: *"MAP:Baro ratio is recommended for new tunes."*

The reboot hazard that makes Baro risky on single-sensor boards **does not apply here** — the UA4C's baro comes from a dedicated atmospheric sensor, not the manifold, so even a mid-drive reboot reads true baro.

**Conversion (preserves NA fueling exactly):**
```
VE_true(row) = VE_old(row) × (baro_ref / MAP_of_row)     # baro_ref = 100
```
The 100 kPa row is unchanged (×1.0). Verified at build time: Off-mode and Baro-mode variants delivered **identical pulsewidth within 1.08% (rounding only)** at every one of the 256 cells.

---

## 4. Injector headroom (verified)

- 425 cc/min × 0.745 g/cc = **5.28 mg/ms** delivered.
- Air/cyl/cycle @ VE100, 100 kPa, 20 °C ≈ 535 mg → stoich fuel 36.4 mg → **6.90 ms** to deliver it. **Matches `reqFuel=6.9` exactly** → the tune is correctly scaled for these injectors.

**Fixed-regulator derate** (fuel pressure doesn't rise with boost; flow ∝ √ΔP):

| MAP | Boost | ΔP across injector | Eff. flow | Duty @ redline |
|---|---|---|---|---|
| 100 kPa | 0 | 43.5 psi | 425 cc | ~45% |
| 150 kPa | ~7 psi | ~36 psi | ~389 cc | **~82%** |
| 175 kPa | ~11 psi | ~33 psi | ~369 cc | **~100% (maxed)** |

**Conclusions:**
- 425cc yellows comfortably support the **150 kPa target**; **~175 kPa is the ceiling** at high rpm. The existing `boostLimit=160` is well-judged — **leave it ~160** with the fixed regulator.
- The single highest-value upgrade for more boost is a **1:1 boost-referenced FPR** (keeps flow at 425cc, drops 150 kPa duty to ~72%).

---

## 5. The new load axis

One unified 16-point load axis for VE, AFR, and spark (kPa):

```
20, 26, 30, 36, 40, 46, 50, 60, 70, 86, 100, 120, 140, 160, 180, 200
```

- Bottom bin raised **16→20 kPa** so the Baro conversion `VE×(100/MAP)` stops overflowing 255 in the deep-vacuum row (overrun/fuel-cut territory — no real loss).
- **86, not 85:** TunerStudio stores MAP bins in 2 kPa steps and quantizes 85→86 on save; using 86 keeps generator re-runs round-trip stable.
- Bins ≤100 re-interpolate the existing NA tune (idle/cruise preserved).
- Bins 120–200 are the new boost rows; **200 sits above what the fuel system supports**, as a clamp.

---

## 6. What goes in the boost rows

### Fuel (VE) — Baro/true-VE form
```
VE_boost(rpm) = VE_100kPa(rpm) × (AFR_anchor(rpm) / AFR_target)
```
(`AFR_anchor` is the source AFR table's own 100 kPa target for that rpm column. The MAP scaling is handled automatically by the Baro term, so boost cells are a flat **~100–110% true VE** — exactly what real VE should look like.)

### AFR target (pump 91 — richen for knock/thermal margin)
| MAP | 120 | 140 | 160 | 180 | 200 |
|---|---|---|---|---|---|
| AFR | 12.5 | 12.0 | 11.8 | 11.6 | 11.5 |

*(With `incorporateAFR=No` this table is display/closed-loop-target only — the actual richening is baked into the VE numbers above. The generator writes `afrTable` **and** `lambdaTable` together: they are dual views of the same firmware bytes, and shipping them inconsistent makes the burned values depend on TunerStudio's load order — see §7.3.)*

### Spark — pull timing off the 100 kPa value
```
advance_boost = advance_100kPa − 0.15°/kPa × (MAP − 100)   (floor 8°)
```
Conservative starting point for 91 octane — **must be confirmed with knock/dyno**.

**Knock-blind extra pull (active):** because the knock sensor is currently unreadable (§7.1), the generator pulls an **extra 3.5° from every boost row** on top of the slope — 140 kPa ≈22→18°, 160 kPa ≈19→16°. Controlled by the generator's `KNOCK_BLIND` flag; set it `False` and regenerate once a knock conditioner is fitted and calibrated.

---

## 7. Settings: safety patches, commissioning patches, first-start fixes

### 7.1 Boost-safety patches (2026-06-08/09, in the generator)

Two gaps found by review and **adversarially confirmed** against the Speeduino `.ini` help text:

**IAT timing retard — was zero, now:**
| Intake °F | 110 | 130 | 150 | 170 | 190 | 210 |
|---|---|---|---|---|---|---|
| Pull ° | 0 | 2 | 4 | 6 | 8 | 10 |

No pull during normal warm running, then ~1°/10°F — thermal protection for heat-soak on repeat pulls.

**Knock window — was effectively off in boost, now extended:**
| Setting | Was | Now |
|---|---|---|
| `knock_maxMAP` | 100 kPa | 250 kPa |
| `knock_maxRPM` | 1000 rpm | 7000 rpm |
| `knock_maxRetard` | 1° | 4° |

> ⚠️ **`knock_mode` is OFF in the first-start tune.** The sensor is a **raw piezo wired
> directly** to the analog input — Speeduino cannot read that (it expects a conditioned
> 0–5 V signal from a TPIC8101-based module or a Phormula KS-4). With a raw sensor on the
> pin, Analog mode could only produce noise-triggered retard and false confidence. The
> window settings above are kept in the file so re-enabling is just `knock_mode → Analog`
> once a conditioner (band-pass ≈ 6.9 kHz for the BP's 83 mm bore) is installed and the
> threshold is calibrated at clean WOT. Until then: conservative timing (the §6 knock-blind
> pull), rich AFR, ears.

### 7.2 Commissioning patches (2026-06-09, `patch_commissioning_settings.py`)

Setup-specific research (Speeduino wiki/forum, miataturbo.net, this project's
`mainController.ini`) cross-checked against a full settings inventory of the draft:

| Setting | Was | Now | Why |
|---|---|---|---|
| `knock_mode` | Analog | **Off** | Raw sensor unreadable — §7.1. |
| `engineProtectType` | Spark Only | **Both** | Spark-only protection cut keeps injecting fuel into a hot exhaust. |
| `afrProtectEnabled` | Off | **Fixed mode** | Lean backstop; the wideband IS wired to the ECU. Fixed mode = absolute max-AFR ceiling (more predictable than table-deviation on an untuned car). |
| `afrProtectMAP` | 180 kPa | **124 kPa** | 180 was **above the 160 boost cut — it could never trigger**. 124 covers the whole boost region and is unreachable NA (no nuisance cuts while NA tuning). |
| `afrProtectRPM` / `TPS` / max AFR / cut time | 4000 / 80% / 1.4 dev / 0.7 s | **2500 / 50% / 13.0 abs / 1.0 s** | Boost builds before 4000 rpm and at part throttle; 13.0:1 ceiling vs 11.5–12.5 targets ≈ 1+ AFR headroom. |
| `mapSample` | Instantaneous | **Cycle Average** | The ini's own help: Cycle Average recommended for >2 cylinders. Instantaneous = spiky load → jumpy fuel. |
| `boostEnabled` | On | **Off** | Commissioning is wastegate-spring-only; re-enable at the boost ramp phase. |
| `fpPrime` | 0 s | **3 s** | Pump never primed at key-on. |
| `primePulse` | all 0 | **8→2 ms by temp** | Priming disabled = hard first catch (forum-documented issue with 425 cc injectors). |
| ASE (`asePct`/`aseCount`/taper) | all 0 | **35→10 % for 10→3 s, 2 s taper** | No afterstart enrichment = catch-then-stall. Starting estimates. |
| `ADCFILTER_*` | all 0 (raw) | **ini-recommended values** | Zero filtering = noisy sensor reads everywhere. |

### 7.3 First-start fixes (2026-06-12, in the patch script + generator)

A line-by-line pre-start review found one fatal and several important problems in the
shipped first-start file. All fixes below are **verified in-file** and were adversarially
reviewed (3 reviewers; every finding independently refuted-tested and reproduced).

| Setting | Was | Now | Why |
|---|---|---|---|
| `wueRates` | **ALL ZEROS — fatal** | 160→100% curve (bins −40→171 °F unchanged): 160/154/148/142/132/122/114/108/103/100 | WUE is a fuel **multiplier** that clamps to its last value → total correction 0 → **zero fuel at any coolant temp; the engine could not start**. The 2026-06-09 audit (§8) described this fix but it never made it into the patch script. Generic BP starting curve — trim during warmup logging. |
| `engineProtectMaxRPM` | 7000 | **1500** | 7000 was above the 6800 rev limit; ini: *"At this RPM and below, engine protections will NOT be active"* → **the boost cut and AFR cut could never fire**. 1500 (not higher) because the firmware gates the boost cut behind it and a lugging low-rpm WOT pull can overboost the small TD03L turbine; protection events also limp to this rpm. AFR protect keeps its own 2500 rpm floor — no nuisance cuts. |
| Accel-enrichment scalars | all 0 | `aeTime` 150 ms, `taeThresh` 50 %/s, `taeMinChange` 2%, taper 1000→5000 rpm, `decelAmount` 100% | `aeTaperMax=0` fully tapered AE away at all rpm (lean tip-in stumble); `decelAmount=0` cut **ALL fuel on every throttle close** (ini: 100% = no reduction). The `taeRates` curve was already populated. |
| `primingDelay` | 0 | **3.0 s** (after `fpPrime`) | Priming squirt fired into an unpressurized dry rail at key-on, wasting the dry-port wetting fix. Procedure: key-cycle 2–3 times before first crank (checklist Phase 5). |
| `crankingEnrichTaper` | 0.1 s | **1.5 s** | Abrupt ~35% fuel step at the crank-to-run handoff invited a stall at catch. |
| `perToothIgn` | No | **Yes** | "Use new ignition mode" — the Speeduino wiki for the Miata 99-05 decoder requires it; with only 4 crank teeth/rev, timing otherwise scatters several degrees. No power-cycle needed, a burn suffices; verify with a timing light afterward. |
| `iacPWMrun` | No | **Yes** | Run the idle valve before RPM sync while cranking — ini: "can help starting the engine by letting more air in." |
| `idleTaperTime` | 0 | **1.0 s** | Idle valve snapped from crank duty (83%) to the run table instantly at catch; short taper smooths the handoff. |
| VE 700 rpm lean trough | VE 59–74 at 60–100 kPa | **Floors 95/90/85/80** (60/70/86/100 kPa) | The unproven NA estimate fell to VE 59–74 in the 700 rpm column (first-catch / stall-recovery path) vs 100–143 at 500 rpm — lean bog/stall risk. Floors lift only lean cells; the rich 500 rpm catch cells were deliberately NOT cut; boost rows re-anchor automatically. |
| Idle spark slope | 13–14° @500 rpm | **Floor 16°** (500 rpm column, 30–46 kPa rows) | Advance fell from ~18° @1000 rpm to 13–14° @500 — destabilizing as rpm sags (idle-advance control is Off). |
| Boost spark | per-kPa slope only | **extra −3.5° all boost rows** | Knock-blind pull, §6 (140 kPa ≈22→18°, 160 ≈19→16°), until a conditioner is fitted. |
| `lambdaTable` | stale NA values (λ≈0.89–0.905 = AFR 13.1–13.3 while `afrTable` said 12.5–11.5) | **synced to `afrTable`** | Same firmware bytes; inconsistent views make burned values depend on TunerStudio load order (the old generator had this bug). |

The VE/idle-spark floors live in the generator behind `FIRST_START_SHAPING`; set it
`False` and regenerate after the NA region is road-tuned (the wideband will have fixed
the trough properly). The knock-blind pull is behind `KNOCK_BLIND` (§6).

### 7.3b Coverage sweep (2026-06-12, every constant in the file; in the patch script)

A 50-agent sweep over all 808 constants (complement to the lens review — hunting the
all-zero base-tune-conversion disease that caused the WUE/AE/priming bugs). 14 findings
confirmed, 8 refuted:

| Setting | Was | Now | Why |
|---|---|---|---|
| `injAng` / `injAngRPM` | all 0 | **355° at 500/2000/4500/6500 rpm** (firmware defaults) | Injection END angle — 0 meant the spray was phased to TDC-firing at all rpm instead of just before the intake event. Not fatal, but degrades cold-start mixture prep and idle: the exact regimes being commissioned. |
| `boostSens` | **65535 (0xFFFF, uninitialized — 13× ini max)** | 2000 (default) | The LIVE closed-loop boost gain the moment Phase 7 flips `boostEnabled` On — 65535 would slam the MAC valve between extremes (boost oscillation into the 160 kPa cut). Consider starting 1000–1500 for the first closed-loop ramp. |
| `boostIntv` | 100 ms | **30 ms** | Ini guidance: 50–100% of the 34 Hz valve period (~15–30 ms). At 100 ms the PID corrected once per ~3.4 valve cycles — sluggish on spool, overshoot-prone. |
| `tpsBinsBoost` | 100→0 (descending) | **0→100 ascending** | Invalid bin order for the firmware table lookup; masked today only because all boost-table rows are identical. Fixed before Phase 7 tuning makes rows differ. |
| `aeColdPct` (+ taper temps) | 0 (taper −40/−40) | **100%**, taper 32–140 °F | AE×0 multiplier when cold — inert only because the taper temps were degenerate. Defused before cold-weather NA tuning trips it. |
| `fuelTrim1–4Table` | −128% every cell | **0%** | Inert (`fuelTrimEnabled` No, and trims only run under Sequential layout) — but −128% = full lean cut on every channel if ever enabled. Neutralized; axes stay unset until trims are really used. |
| `tachoDuration` | 0 ms (below ini min) | **2 ms** | Set to a valid default (was below the ini minimum). **Mostly moot:** RPM is read by the TunerStudio dash (Raspberry Pi) over the serial data link, not from the hardware tach output — the tach pin is likely unwired. Harmless either way. |
| `boostFreq` | 34 Hz | **30 Hz** | Vehicle-specific research: MAC 35A-type 3-port valves lose plunger travel margin near 34 Hz (msextra field report: control loss >~33 Hz; Miata builds run 19.5–26 Hz; AEM uses 31). ⚠️ Takes effect only after an **ECU power-cycle**. |

**Latent traps documented, deliberately NOT changed:**
- `hardRevMode` must stay **"Fixed"** — the coolant-based rev curve (`coolantProtRPM`/`coolantProtTemp`) is conversion garbage reading **700 rpm at every temperature**; switching the limiter mode to "Coolant based" without populating it = a 700 rpm rev limit.
- `fuelTrimEnabled` stays **No** until the trim tables get real axes (cells are now neutral 0%).
- Phase 7 boost prep verified sane: closed-loop base-duty table ramps 20→50% with no 100% cells; keep `boostDCWhenDisabled = 0%` for the first ramp (valve unpowered = pure wastegate spring below the enable threshold).

**Vehicle-specific research (2026-06-12) — confirmed for this car:** injAng 355° flat (ends the squirt ≈ the BP's intake-valve opening — the best paired injection can do; Miata sequential consensus is EOI just before IVO); 500 Hz NB idle valve (the "needs a converter" caveat is MS2-only; Speeduino drives it natively, usable duty ~20–80%, verify polarity at bench test); aeCold and idle taper neutral/safe. Dash is a **TunerStudio dash on a Raspberry Pi** (RPM/gauges over the serial data link — no factory cluster, so the hardware tach output and its pulse format are irrelevant). **Open hardware question:** which boost solenoid is installed and how its 3 ports are plumbed — all boost advice assumes a MAC 35A with solenoid-dead = spring-only failure mode; confirm before Phase 7.

### 7.4 Verified correct — leave alone

Researched and deliberately unchanged (2026-06-09 audit + settings research):

- **Trigger:** Miata 99-05 pattern, crank speed, `TrigAng 0°`, both edges RISING — matches the wiki for this decoder exactly. If the timing light is a few degrees off, **trim `TrigAng`**; if it's way off, suspect wiring/sensor or swapped coil pairing (1–4 vs 2–3) — **never flip the trigger edges** (see the audit correction in §8).
- **Spark output:** "Going Low" (correct — the wrong value destroys IGBTs); wasted spark 1–4/2–3; dwell 3.0 ms run / 4.0 ms crank, standard for NB coils (raise cranking dwell to ~5 ms only if weak-spark hard-starting shows up); cranking advance locked at 5° (`ignCranklock` On).
- **Injectors:** yellows flow ~425–450 cc @ 3 bar (Denso 195500-4450); `reqFuel 6.9` consistent (§4); `injOpen 0.9 ms` in the practical 0.8–1.0 ms community range (OEM data ~0.55 @ 14 V; battery-correction curve present). Fine for first start; refine later.
- **Idle valve:** `idleFreq 500 Hz` — correct for the 99+ Miata PWM IAC (hums below 250 Hz). Open-loop PWM, crank duty 83%, run 90→75% — sane starting points.
- **Rev limits:** 6500 soft / 6800 hard — fine for stock rods.
- **EGO:** closed-loop OFF — correct through all tuning; **never enable in boost**.

Deferred to later phases: DFCO (enable only after idle is stable), closed-loop idle, idle advance, AE retune.

---

## 8. Audit & review history

### 2026-06-08/09 — build reviews
- Code/bug review (structure, table orientation, interpolation, XML): clean; found + fixed the Baro 16 kPa bottom-bin clip (§5).
- Tuning review: flagged the knock + IAT gaps (§7.1) and the untuned-anchor dependency (§10).
- Adversarial review: tried and failed to refute the knock/IAT findings — both confirmed via canonical `speeduino.ini` help strings.

### 2026-06-09 — first-start audit *(folded from ECU_FIRST_START_AUDIT.md, since retired)*

Point-in-time audit of the boost draft against researched specs for this exact hardware.
**Verdict: the tune as then shipped could not start the engine.**

- **Fatal:** `wueRates` all zeros (in the NA source *and* the drafts) → zero pulsewidth at any coolant temp; nothing in the composite logger or fuel-pressure checks would explain the no-fire. ⚠️ The audit prescribed the fix, but **it never made it into the patch script** — the shipped file still had zeros until the 2026-06-12 fixes landed it for real (§7.3).
- **Start-quality gaps:** `fpPrime`, `primePulse`, ASE all zeros → hard start, catch-then-stall. Fixed in §7.2.
- **Verified-correct findings:** consolidated into §7.4.
- ⚠️ **Correction to the audit's trigger advice:** the audit said to flip the RISING edge if the timing light shows wrong advance. That **contradicts the wiki** — both edges stay RISING for this decoder. A few degrees off → trim `TrigAng`; way off → suspect wiring/sensor or swapped coil pairing (1–4 vs 2–3), not edges. (§7.4 has the corrected guidance.)
- Diagnostic rule of thumb kept from the audit: if it cranks 5+ s without firing, log RPM + pulsewidth — PW = 0 means a corrections problem; PW > 0 with no fire means spark/trigger.

Sources: [Speeduino Warmup manual](https://wiki.speeduino.com/en/configuration/Warmup) ·
[Miata 99-05 decoder](https://wiki.speeduino.com/en/decoders/Miata_99) ·
[RX-8 yellow review (miataturbo.net)](https://www.miataturbo.net/diy-turbo-discussion-14/rx8-yellow-denso-195500-4450-425cc-pnp-review-67140/) ·
[RX-8 injector deadtime (msextra)](https://www.msextra.com/forums/viewtopic.php?t=76100) ·
[NB idle in TunerStudio (mx5nutz)](https://www.mx5nutz.com/threads/nb-idle-control-in-tunerstudio.57913/) ·
[Miata PWM idle frequency tests (miata.net)](https://forum.miata.net/vb/showthread.php?t=172015)

### 2026-06-12 — first-start fixes + adversarial review
Line-by-line review produced the §7.3 fixes (including landing the WUE fix the audit had
only described). Three reviewers; every finding was independently refuted-tested and
reproduced before the fix shipped. All fixes verified present in
`TurboExo_FirstStart.msq`. The live tune was loaded into TunerStudio the same day
(`CurrentTune.msq` now tracks it — see §9) and the off-mode draft + standalone `.table`
exports were deleted (no longer produced by the generator).

### 2026-06-12 — full-coverage sweep
Complement to the lens review: 6 reviewers covered **every one of the 808 constants**
(each accounted for as settled / disabled-with-no-roadmap / evaluated against the ini),
findings gated by the same refute+reproduce verification. Produced the §7.3b fixes —
notably `boostSens` 0xFFFF and the `injAng` zeros — and the documented latent traps.
8 further claims were raised and refuted (e.g. rolling-cut tables, hardware-test pulse
widths: real zeros, no consequence on any roadmap path).

---

## 9. Files & regeneration pipeline

| File | What |
|---|---|
| **`TurboExo_FirstStart.msq`** | **← Load this for first start.** Boost-extended Baro draft + all §7 settings. |
| `CurrentTune.msq` | TunerStudio's **live working tune** — rewritten on every save. As of 2026-06-12 it holds the loaded first-start tune (NOT the original NA estimate; that's preserved at `restorePoints/TurboExo_2026-06-12_13.21.07.msq`). After NA road tuning it will hold the tuned tune — which is exactly what the generator reads by default. |
| `CurrentTune_BOOST_DRAFT_BARO.msq` | Intermediate generator output / patch-script input. Regenerated by the pipeline below; don't hand-edit. |
| `generate_boost_tables.py` | Boost-table generator. **Axis-agnostic and multiplyMAP-mode-aware** — it reads whatever load axis the source has and detects Off vs Baro mode, so it is safe (verified idempotent) to re-run on Baro-mode/patched tunes. Writes `afrTable` and `lambdaTable` together (§7.3). Flags to flip later: `FIRST_START_SHAPING=False` after NA road tuning; `KNOCK_BLIND=False` after a knock conditioner is fitted. |
| `patch_commissioning_settings.py` | Applies all §7.2/§7.3 scalar+curve settings. **ALWAYS re-run it after the generator** so they persist into every regeneration. |

```
python3 generate_boost_tables.py [source.msq] [output.msq]
        # defaults: CurrentTune.msq → CurrentTune_BOOST_DRAFT_BARO.msq
python3 patch_commissioning_settings.py
        # CurrentTune_BOOST_DRAFT_BARO.msq → TurboExo_FirstStart.msq
```

The scripts' docstrings are the canonical description of their behavior; these notes only
summarize.

---

## 10. Open items / before you boost

The required workflow: commission the car (`FIRST_START_CHECKLIST.md`), tune the full NA
region on the wideband, **then regenerate the boost rows** from the real anchor.

1. **Tune the NA VE table first, including the 100 kPa WOT row.** Every boost cell is extrapolated from that row. Then re-run the §9 pipeline with `FIRST_START_SHAPING=False`.
2. **Knock protection needs hardware first:** a conditioner module (TPIC8101-based or Phormula KS-4) between the raw sensor and the analog input, then `knock_mode → Analog`, threshold calibration at clean WOT, and `KNOCK_BLIND=False` + regenerate. Until then: conservative timing, rich AFR, ears.
3. **Fit an analog oil-pressure sender BEFORE the boost-ramp phase.** `oilPressureEnable`/`oilPressureProtEnbl` are currently Off, calibration zeros, pins parked at A0. Use a spare UA4C analog input; when wiring, **verify no pin collision with the raw knock-sensor wire**. Then populate `oilPressureProtMins`/`RPM` (e.g. ~7/15/25/35 psi at 1000/2500/4000/6000 rpm) and `oilPressureProtTime` ~0.5–1.0 s. Fuel-pressure protection is similarly available if a sender is ever fitted.
4. **Bring boost up incrementally**, watching wideband AFR and listening for knock. Re-enable `boostEnabled` first (OFF for commissioning — spring only).
5. Confirm wastegate/solenoid targets ~150 kPa with 160 as the hard cut; expect possible nuisance boost-cut if the solenoid overshoots — small margin between target and cut.
6. Consider a **boost-referenced FPR** before going past ~160 kPa (§4).
