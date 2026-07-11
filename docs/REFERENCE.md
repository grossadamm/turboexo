# TurboExo Reference — pinned ground truth

Stable facts so agents don't re-derive or re-research them. Chronological history
lives in `EXPERIMENT_LOG.md`; current front line in `STATUS.md`.

## The rig
- Vehicle: 1999 Mazda Miata NB1, 1.8 L BP-4W, 1839 cc, 4-cyl, firing order **1-3-4-2**.
- Forced induction: external **TD04L-13T** turbo. The build was rewire + turbo only; internals known-good (ran before).
- ECU: **Speeduino UA4C, firmware 202501**. Speed-density, wasted spark, paired injection (`injLayout` = Paired, `inj4CylPairing` = "1+4 & 2+3").
- Link: `/dev/cu.usbmodem101` @ 115200. A **data** USB cable is required — charge-only cables enumerate nothing.
- Log tooling: `npx mlg-converter --format=csv <file>.mlg` → semicolon CSV in `DataLogs/`.
- Hidden TS Hardware Test page: enable via `projectCfg/project.properties` (`enablehardware_test`).

## Injectors & reqFuel
- Installed: RX-8 "yellow" **Denso 195500-4450** — **425 cc/min @ 43.5 psi** (3 bar); ~500–524 @ 4 bar. Resistance 11.8–16.5 Ω.
- Stock 1999 "red" **Denso 195500-3310** — **238 cc/min @ 43.5 psi** (~280 @ the NB's ~58 psi rail).
- **reqFuel** = factory 12.7 (GitHub-verified) × 238/425 ≈ **7.0–7.1 ms**. Fuel pressure cancels (same √-ratio at any common rail pressure). Empirically 7.0 was the only value that ran. **Current = 7.1.**
- ⚠️ **265 cc is the wrong injector** (01–05 purple / 94–97 tan). It yields 7.9 (~13% rich).

## Injector dead time (RX-8 yellow, measured, ~atmospheric)
| Voltage | Dead time |
|---|---|
| 14.0 V | 0.55 ms |
| 12.75 V | 0.70 ms |
| 11.5 V | 0.86 ms |
| 10.25 V | 1.15 ms |
| 9.0 V | 1.48 ms |
| 7.75 V | 2.02 ms |
| 6.5 V | 3.03 ms |

`injOpen` = 0.9 ms is a ~11.5–12 V value; at 9–10 V cranking the real dead time is 1.15–1.48 ms, so cranking fuel is voltage-sensitive — another reason to keep the battery charged.

## Wideband / AFR
- Spartan 3 OEM, custom-linear cal: **0 V = 10.0 AFR, 5 V = 20.0 AFR**.
- Warmup sequencer holds fixed cal voltages until exhaust ~350 °C: **≈1.66 V = 13.3 AFR**, second plateau ≈16.5 — the source of the pinned 13.1–13.2 in logs.
- **AFR echo:** `readO2()` always logs raw sensor as AFR; `calculateAfrTarget()` returns live O2 as *Target* while `runSecs <= ego_sdelay` (`runSecs` resets each crank). On short catches Target shadows AFR → logged AFR is **not** mixture. Valid only after ~15 s+ running exhaust heat. Brown wire = heater status (2 V = sensor valid).

## Target operating envelope
| Item | Value | Note |
|---|---|---|
| Cranking MAP, closed throttle (healthy) | 80–95 kPa | observed 62–71 = air-path deficit (IACV) |
| Warm idle MAP (healthy) | 28–37 kPa | >~40–45 warm ⇒ suspect vacuum leak |
| reqFuel | 7.0–7.1 ms | see above |
| Spark plugs | NGK BKR7E (#4644), gap 0.030" | 2 steps colder for turbo |
| IACV | 8.7–10.5 Ω, PWM ~500 Hz, 2-wire low-side, fails closed | `iacAlgorithm` = PWM Open loop |
| Ignition polarity | `IgInv` = "Going Low" | never "Going High" (holds coils energized/hot) |
| Flood clear | TPS > 90 % → PW 0 | `tpsflood` = 90 |
| stoich | 14.7 | |

## Key tune constants (CurrentTune.msq)
| Constant | Value | Note |
|---|---|---|
| reqFuel | 7.1 | 238/425 derivation |
| divider | 2 | PW ≈ reqFuel/2 × VE × MAP × Gammae + injOpen |
| injOpen | 0.9 ms | dead time (see curve) |
| multiplyMAP | Baro | speed-density MAP term |
| battVCorMode | Open Time only | Whole PW added ~12% at cranking V — avoid |
| crankingEnrichTaper | 0.1 s | tension: 3.0 s drowns over repeated cranks, 0.1 s may starve a clean catch |
| CrankAng | 10° | cranking advance (MS3 reference uses 12°) |
| iacAlgorithm / iacPWMdir | PWM Open loop / Normal | **`iacStepperInv` is a no-op** (stepper only) |
| engineProtectMaxRPM / Type | 1500 / Both | ⚠️ hard fuel+spark cut at 1500 — **raise before any sustained-idle attempt** |
| dfcoEnabled | Off | no overrun fuel cut |
| egoAlgorithm | No correction | open loop (wideband unusable in warmup) |

## veTable format
- 16×16. **Rows = load** (`fuelLoadBins`: 20, 26, 30, 36, 40, 46, 50, 60, 70, 86, 100, 120, 140, 160, 180, 200 kPa); first row = lowest load. **Columns = RPM** (`rpmBins`: 500, 700, 900, 1500, …).
- Idle-region cells (500–700 rpm × 40–70 kPa) must stay near the `VEfix` values (~46–52) or you re-create the **idle-vacuum trap** (forced-high VE → ~2× fuel as MAP falls → floods, can't reach idle vacuum).

## Verified good vs open suspects (as of 2026-07-11)
**Verified good:** trigger / full sync (status 2, 0 loss), spark all cylinders, base timing (yellow ≈6° vs commanded 5°), MAP plumbing + sensor, fuel pressure, injectors pulse, grounds/ECU power (battery charged), `IgInv` "Going Low", idle PWM config matches factory.

**Open / suspect:**
- Battery discipline — recent cranks 9.6–10.3 V; no alternator charge since 07-09.
- IACV airflow — powered but MAP unchanged closed-throttle; verify `iacPWMdir` polarity, stuck/carboned valve.
- Cylinder #2 — sooty on a fresh plug; hardware (swap injector #2↔#1 to isolate).
- `engineProtectMaxRPM` 1500/Both — raise (~2800) before holding an idle.
- Wideband — usable only after ~15 s+ exhaust heat.

## Tune file lineage
| File | What it is |
|---|---|
| `TurboExo_FirstStart.msq` | first-start tune (WUE fatal-zero fixed, etc.) |
| `TurboExo_VEfix_2026-07-09.msq` | **last-known-good**; factory-transplant VE; the 07-09 run (1212 RPM); reqFuel 7.0 |
| `TurboExo_reqFuel85_2026-07-09.msq` | reqFuel 8.5 (refuted — too rich) |
| `TurboExo_crankVE_2026-07-10.msq`, `TurboExo_crankwall_2026-07-10.msq` | idle-region VE inflation (caused the idle-vacuum trap; since reverted) |
| `TurboExo_crankAdv10_2026-07-10.msq` | CrankAng 5→10 |
| `TurboExo_crankfuel_2026-07-11.msq` | reqFuel 7.9 state (pre-lean-out) |
| `TurboExo_idleleanout_2026-07-11.msq` | **current**: reqFuel 7.1 + idle VE cells reverted to VEfix |
