# TurboExo Experiment Log — no-start → first-idle campaign

1999 Miata NB1 1.8 (BP-4W), TD04L-13T external turbo, Speeduino UA4C (fw 202501), 420cc "RX-8 yellow" injectors (Denso 195500-4450), speed-density, wasted spark + paired injection (1+4 / 2+3), TunerStudio dash on a Pi. Engine ran fine before the build; the build was **rewire + external turbo only** (internals known-good).

Chronological, newest last. Entries marked ~~struck~~ or "REFUTED" are kept deliberately — several conclusions were later overturned and the corrections matter.

---

## 2026-04-03 — Corrupted factory reference (found retroactively 2026-07-11)
- **Change/Action:** Factory Speeduino base tune (`Miata_PNP99-00_SpeedyEFI.msq`) re-saved via TunerStudio; **reqFuel edited 12.7 → 14.7** (restorePoints show 12.7 at 17:07, 14.7 at 17:48 that day).
- **Why/Hypothesis:** Unrecorded April experiment.
- **Result/Evidence:** GitHub commit history of speeduino/Tunes: reqFuel = **12.7 in every revision, never 14.7**. The ~/Downloads copy carried the edit forward and later anchored the bad "8.5" derivation (see 07-09/07-11).
- **Verdict:** Confirmed corruption. Rule: never re-derive from the Downloads copy; fetch raw from GitHub.

## 2026-06-09 — "No proven NA baseline" reset
- **Change/Action:** Reframed the project from "tuning" to "commissioning a never-started engine" (on Speeduino). Knock input confirmed raw/unusable → knock mode OFF; wideband analog confirmed wired to ECU.
- **Why/Hypothesis:** Earlier boost-table work had wrongly assumed `CurrentTune.msq` was road-proven.
- **Result/Evidence:** All boost rows declared placeholders pending NA tuning.
- **Verdict:** Confirmed; still governs the plan (regen boost tables after NA tuning).

## 2026-06-12 — WUE fatal-zero fix + adversarial tune reviews → `TurboExo_FirstStart.msq`
- **Change/Action:** Found `wueRates` **all zeros** (warm-up enrichment is a multiplier → PW=0 → zero fuel at any temp) — the fix claimed on 06-09 never made it into the patch script. Fixed (160%→100% curve). 21-agent review confirmed 9/9 findings: `primingDelay` 0→3 s, `engineProtectMaxRPM` 7000→1500, `decelAmount` 0→100%, accel-enrich zeros populated, stale `lambdaTable`, etc. A second 808-constant coverage sweep added 13 more fixes (notably `injAng` 0→355°). AFR ECU cal set: Custom Linear WB **0 V = 10.0, 5 V = 20.0 AFR**. Also: `iacPWMrun` Yes, `idleTaperTime` 1.0 s, dwellLim 7→8 ms (06-13).
- **Why/Hypothesis:** The generated first-start tune inherited "all-zero disease" from the base-tune conversion.
- **Result/Evidence:** Diffs verified in-file; `TurboExo_FirstStart.msq` burned. Spartan 3 OEM in free air read 16.6 (~3.3 V) instead of ~20 — parked for hardware debug.
- **Verdict:** Confirmed (the WUE bug alone was a guaranteed no-start).

## 2026-06-17 — First crank attempt: RPM dead-flat 0
- **Change/Action:** First real crank. No start; TunerStudio RPM gauge never moved.
- **Why/Hypothesis:** With TS connected and starter spinning, RPM=0 ⇒ no decoded crank-trigger signal.
- **Result/Evidence:** Log `2026-06-17_18.07.20.mlg`. Corrected a bad assumption: NB1 crank/cam are **open-collector Hall** (4-tooth crank, 3-tooth cam), not the NA's optical CAS. UA4C jumpers physically verified correct (JP2/JP3 = direct/Hall, JP4/JP5 pull-ups ON) → board ruled out; fault upstream in wiring.
- **Verdict:** Confirmed trigger-path fault (wiring, not board or tune).

## 2026-06-20 — Charge-only USB cable + trigger wiring fix → first RPM
- **Change/Action:** ECU wouldn't enumerate on the laptop → **charge-only USB cable** was the culprit; a data cable restored `/dev/cu.usbmodem101` @115200. User then found and fixed the upstream **trigger wiring fault** (exact fault not recorded).
- **Result/Evidence:** Log `2026-06-20_16.56.09.mlg` — RPM reads while cranking; engine attempted to turn over.
- **Verdict:** Confirmed — Phase 1 (trigger) cleared. *(Note: the trigger fix was 06-20, not 06-28.)*

## 2026-06-21 — Full sync confirmed; cranks/fires/won't catch; plugs condemned
- **Change/Action:** Log review: **Sync status 2, 0 sync loss, stable cranking RPM**. Symptom now: pop/cough, smells rich, throttle helps, won't run. Plugs pulled: all sooty black, #3 slightly wet, gaps looked wide → ordered **NGK BKR7E (stock #4644), gap 0.030"** (2 heat ranges colder for turbo), plus new coils and a new wideband.
- **Why/Hypothesis:** Wide gap + low cranking dwell (4 ms) = weak spark; black plugs = plenty of fuel.
- **Result/Evidence:** Subagent found the **official factory base tune** (`Miata_PNP99-00_SpeedyEFI.msq`, speeduino/Tunes) — idle PWM config matches TurboExo exactly (PWM open-loop, 500 Hz, iacStepperInv Yes); cranking enrich 225/195/175/125% matches; ASE (35/28/18/10%) richer than factory 15%/1.0 s. reqFuel 6.9 judged "OK for 420cc" — **later superseded twice** (see 07-09, 07-11). Also rejected a downloaded NB2 PNP tune (wrong board/pinout/VVT).
- **Verdict:** Trigger confirmed done; spark-energy hypothesis pending parts.

## 2026-06-28 — New plugs/coils/wideband installed; MAP frozen → MAC-valve mis-plumb found
- **Change/Action:** Hardware: full replacement of spark plugs, coils, wideband. Cranked: no start, but "more consistent puts." Breakthrough tooling: `npx mlg-converter --format=csv` finally makes .mlg logs parseable.
- **Result/Evidence:** Log `2026-06-28_09.04.26` (42 s): sync loss 0, **catches to 705 RPM**, PW 10–14 ms, but **MAP dead-flat 98–99 kPa the entire log** (two values total). User revealed the MAP vacuum line was on the **MAC boost solenoid**, not a manifold port — pre-throttle never sees vacuum. **Re-plumbed to direct manifold vacuum.**
- **Corrections from adversarial review:** frozen MAP does NOT retard idle timing (advTable1 nearly flat across load at idle — that claim withdrawn); and the log AFR read *lean*, not rich (itself later shown meaningless — see AFR-echo below).
- **Verdict:** Confirmed must-fix (speed-density with a frozen load axis can't run) — necessary but not sufficient.

## 2026-06-28 — Post-MAP-fix log; AFR==Target "echo" discovered
- **Change/Action:** Log `2026-06-28_10.27.59`: MAP now live (76–100 kPa, 23 values). Flood-clear behavior understood (tpsflood 90%: TPS>90 during crank cuts PW to 0 — user was using it deliberately). Catches to 637 but won't sustain. Subagent then proved **logged AFR == AFR Target exactly (0.00 delta) in 100% of firing rows** across all logs → conclusion at the time: "the wideband is not being read; no trustworthy mixture data while firing."
- **Result/Evidence:** Later the same day the sensor read real values engine-off (free air 19.7, breath-test dips) — "live engine-off, echoed while firing."
- **Verdict:** The *observation* (AFR==Target while firing) was confirmed and held in every log through 07-10. The *mechanism* was wrong — **reinterpreted 2026-07-11** (see below). Practical rule stood either way: don't tune fuel from logged AFR on short catches.

## 2026-06-28 — ~~Mechanical-weakness / vacuum-leak pivot~~ (REFUTED)
- **Change/Action:** 3-lens subagent review (ignition/fuel/mechanical) of the day's logs converged on: weak cranking vacuum (MAP only 70–76 kPa closed-throttle) = fresh-rebuild mechanical deficit (cam timing/compression), plus battery sag 6.8–7.4 V.
- **Correction 1 (same day):** engine **ran fine before**; build was rewire + external turbo only → compression/cam timing known-good; hypothesis retargeted to "vacuum leak in new turbo plumbing."
- **Correction 2 (2026-07-09):** **vacuum-leak theory dead** — research (DIYAutoTune/MSExtra): healthy cranking MAP is **80–95 kPa**; the logged 77–84 was *normal*. Leaks only show at warm idle (>~40–45 kPa when 28–35 expected).
- **Verdict:** REFUTED (both versions). Lasting residue: charge the battery before diagnosing anything.

## 2026-06-28 — Base timing CONFIRMED, spark confirmed, banked plug pattern decoded
- **Change/Action:** Timing light while cranking (ECU commands CrankAng 5°): **yellow mark at ~6° BTDC** (NB pulley: yellow = timing mark, white = TDC companion 10° away) → within 1° of commanded. Strobe on #1 and #2 wires flashed.
- **Result/Evidence:** Base timing + TrigAng 0 eliminated as cause. Plug pattern: **1 dark, 2 very dark, 3&4 clean** — but injectors AND coils are both paired 1+4/2+3, so a banked driver/coil fault can't produce a 1&2 split → fault is individual/positional to the front cylinders; with spark on 1&2 confirmed, dark 1&2 = fuel (rich), not spark.
- **Verdict:** Confirmed good: trigger, spark, base timing, MAP (post-fix), fuel pressure.

## 2026-06-28 — Hardware Test page enabled; all 4 injectors pulse; flooded cylinders proven
- **Change/Action:** Enabled the hidden TS Hardware Testing page by editing `project.properties` (`enablehardware_test_OFF` → `enablehardware_test`). User pulsed each injector: **all 4 click**. Coil pulse test (On–Pulsed, ~3 ms): spark on both channels — and one test **lurched the car** (test spark ignited fuel pooled in a cylinder).
- **Verdict:** Injector drivers/wiring/coils electrically confirmed; cylinders confirmed **flooded** — over-fuel narrative reinforced.

## 2026-06-28 — ECU brownout: bad grounds found & fixed; IgInv blunder and reversal
- **Change/Action:** Fuel-pump relay clicking on/off at key-on; TPS dropping out while cranking; log showed **Battery V max 7.6, sags to 0.2 V**. User measured 12.8 V at battery vs **7 V at ECU**, and found coil power wires + coils running **HOT**. Claude blind-recommended flipping `IgInv` to "Going High" — **WRONG and dangerous**: Speeduino output is non-inverting; "Going Low" is correct for the factory NB1 coil pack (Going High holds coils energized). Recommendation researched and reverted same day. Real fix: **user repaired bad grounds/power wiring.**
- **Result/Evidence:** Post-fix log: cranking avg 9.6 V, min 9.2, max 11.2 — healthy starter sag. Hot coils explained by the brownout/undefined output state, not the tune.
- **Verdict:** Confirmed fix (grounds). IgInv stays **Going Low** — permanent rule.

## 2026-06-28 — Trigger regression re-fixed; MAP stuck at 71 → VICS check-valve trap; best run yet (707 RPM, 1.7 s)
- **Change/Action:** After the wiring work, one log showed RPM 0 / sync 0 (knocked trigger wire) — re-fixed. Next log: full sync but **MAP frozen at exactly 71 kPa in all 463 rows** even during 646-RPM catches; pulling the hose gave a "pop" and MAP jumped to 100 → the line held **trapped vacuum** behind the VICS circuit's check valve. **VICS solenoid removed, check valve deleted, MAP run direct to the manifold port (VICS/#1-runner tap), other branches capped.**
- **AFR side:** identified the **Spartan warmup Output Sequencer** — during heater warmup it emits fixed cal voltages (≈1.66 V = 13.3 AFR on the 10–20 cal; a 2nd level ≈16.5) — the source of the pinned 13.2. Brown wire = heater-status output (0/1/2 V; 2 V = sensor valid). After ~60 s powered preheat, free air read **19.7 = sensor at temp**.
- **Result/Evidence:** Log `2026-06-28_17.53.58`: MAP live 70–99, tracking TPS. Log `2026-06-28_20.15.25`: **707 RPM held ~1.7 s** (t=7.3–8.9 s), died as enrichment tapered (PW 9.2→6.4 ms) and only stayed up with TPS 13–16%.
- **Verdict:** MAP plumbing finally fully fixed (confirmed in all later logs). Wideband thermal behavior confirmed.

## 2026-07-09 — Fresh session: battery again, longest run 2.9 s, nervous kill at 1511 RPM
- **Change/Action:** Injector clicks re-confirmed. Three cranking sessions logged.
- **Result/Evidence:** `12.52.50`: battery collapsed to 6.7–7.6 V, peak 612 — battery declared blocking. `12.59.44`: self-sustained ~1 s at 638 (starter released, V climbing). `13.01.33`: **2.9 s run at 625–700 RPM**, starter released, MAP tracked 91→78 and hit **43 kPa** on closed-throttle spin-down (MAP system fully validated); a separate **1511 RPM run was killed by the user** out of nerves — 1500 is normal cold fast-idle; likely the best start yet thrown away. Battery went on tender.
- **Verdict:** Confirmed: MAP good, engine can run; remaining cause in the tune's fuel math.

## 2026-07-09 — ROOT CAUSE: VE table was factory×(100/load) → factory transplant (`TurboExo_VEfix_2026-07-09.msq`)
- **Change/Action:** Bilinear-fit of both possible veTable row orientations against 752–1177 logged "VE Current" samples (mean err 0.4 vs 18.5) proved the table was **factory×(100/load)** — it cancelled the MAP term (multiplyMAP=Baro), delivering ~2.9× factory fuel at idle vacuum: floods at any real vacuum, only fires near-atmospheric MAP. Explains the entire history (needs 10–20% TPS to fire, dark plugs, dies as vacuum builds). **Fix:** VE rows ≤100 kPa transplanted verbatim from the factory tune; boost rows = 100 kPa row ×1.10–1.30 (placeholders). Pre-fix tune preserved: `restorePoints/TurboExo_2026-07-09_19.17.18.msq`. msq convention nailed down: first listed veTable row = LOWEST load bin.
- **Result/Evidence:** Log `2026-07-09_19.20.05`: **best ever — 556→849→1212 RPM, ran ~2.5 s** while the throttle *closed* to 10%, MAP pulled 97→67 (53 min), alternator charging 13.4 V. Stalled decelerating through ~800 RPM (PW 3.1–3.3 ms — lean decel). Next log `19.24.45` never caught (wet plugs, one 26 s crank, battery 7.9 V).
- **Verdict:** CONFIRMED root cause #1 of the no-start. The old "reqFuel 6.9 OK" conclusion exposed as an artifact of the broken table.

## 2026-07-09 — reqFuel 7.0 → 8.5 (`TurboExo_reqFuel85_2026-07-09.msq`) — later refuted
- **Change/Action:** With true factory VE in, PW-model analysis (verified against firmware: PW = reqFuel/2 × VE × MAP × Gammae + 0.9) said 7.0 was **~24.5% lean** vs "factory 14.7 on 265cc". Initial 9.3 revised to **8.5** after bench-flow research: stock NB1 = 238 cc & yellows = 424 cc @43.5 psi → band 8.25–8.66 via **14.7×238/424**. Adversarial reviewer agreed.
- **Result/Evidence:** Log `19.49.27`: reqFuel 8.5 live in ECU, closed throttle, only blips to 686 — battery sagged to 7.0 V and plugs fouled (4th+ session), so not a clean test.
- **Verdict:** REFUTED 2026-07-11 — the 14.7 anchor was the user's own April edit (factory is 12.7); 8.5 is ~8–20% rich. The reviewer's "first real running AFR" support claim also refuted (it was the echo).

## 2026-07-10 — Clean-test protocol exposes trap #2: cranking-VE collapse → crank-wall cells (`crankVE` / `crankwall`)
- **Change/Action:** First fully clean test: **clean plugs, charged battery, cold, closed throttle**. Log `2026-07-10_16.44.46`: fired to 456 RPM, MAP pulled to 62–64 kPa, and VE interpolated down off the factory anti-stall wall (500-RPM column VE=100 only at ≥70 kPa; at 66→78, 64→67, 62→56 — lookup math verified) → PW 8.4→4.2 ms → **died lean**; then partial-fire loop at 240 RPM/66–69 kPa. With-throttle sessions had stayed ~97 kPa, which is why they caught. Fix: `TurboExo_crankVE_2026-07-10.msq` (500-RPM VE at loads 40/46/50/60 → 100), then `TurboExo_crankwall_2026-07-10.msq` (also 700-RPM row 65/75 at 50/60).
- **Result/Evidence:** Log `16.55.58`: fix worked as designed — **VE held 100, PW ~8 ms through every light-off** — but closed throttle produced **zero combustion** while ~11–15% TPS fired immediately (1.9 s at 420–545). More fuel didn't move the threshold.
- **Verdict:** Crank-VE collapse CONFIRMED and fixed; but it revealed the closed-throttle blocker is **air, not fuel**. Cranking MAP 62–68 vs healthy 80–95 → IACV not flowing air.

## 2026-07-10 — MS3 cross-check: cranking advance 5°→10° (`TurboExo_crankAdv10_2026-07-10.msq`); VE transplant verified
- **Change/Action:** Compared against a professional MS3 MM9900 99-00 base tune (not loadable — MegaSquirt — reference only). Raised CrankAng 5→10° (MS3 uses 12°). Subagent independently verified the VE transplant: **SANE** (NA region mean |diff| 1.4 VE vs factory; boost rows smooth; MS3 cross-check within 15 VE). Residual noted: 500 rpm/36 kPa still 36 — cliff if light-off MAP ever dips <38 kPa.
- **Verdict:** Applied; unproven contribution (no catch since).

## 2026-07-10 — IACV found UNPOWERED → powered; did NOT fix it
- **Change/Action:** Research corrected a false lead: the NB IACV bypass is **cast into the throttle body** (no air hose; the valve's two small hoses are coolant) — so "misrouted bypass hose" was impossible. User then found the **IACV had no 12 V feed** (previously confused with the removed VICS solenoid) and powered it — audible whine at key-on.
- **Result/Evidence:** Logs `17.32.24`/`17.33.47`: closed-throttle cranking MAP **still 67 kPa** — identical to unpowered; still fires only with throttle. "Powered + whining proves electrons, not airflow."
- **Verdict:** Necessary fix, but REFUTED as the blocker. Remaining suspects: PWM polarity (`iacStepperInv`), valve stuck/carboned, base-air path.

## 2026-07-11 — AFR-echo REINTERPRETED (firmware source): the AFR channel was real all along
- **Change/Action:** Read Speeduino 202501 source: `sensors.cpp readO2()` **always** logs the raw calibrated sensor as AFR; the echo runs the other way — `corrections.cpp calculateAfrTarget()` returns live O2 as the *Target* while `runSecs <= ego_sdelay`, and runSecs resets on every cranking event, so on short catches **Target shadows AFR**, not vice versa.
- **Result/Evidence:** Log audit: catches dominated by flat 13.1–13.2 (498/647 rows in `19.20.05`) and 16.4–16.5 = **Spartan warmup-sequencer cal voltages** (heater deliberately held off until exhaust ~350°C — condensation protection). So logged AFR during catches was the real pin voltage, but mostly **not mixture** — no ECU setting can fix it; needs ~15 s+ of running exhaust heat.
- **Verdict:** CONFIRMED reinterpretation. Practical outcome unchanged: no usable mixture data on brief catches. Optional cosmetic change (ego_sdelay=0 + egoAlgorithm "No correction") so Target stops shadowing and liveness is visible.

## 2026-07-11 — reqFuel anchor audit → 7.9 + battVCor "Open Time only" + taper 0.1 s (`TurboExo_crankfuel_2026-07-11.msq`, LOADED)
- **Change/Action:** GitHub history proved factory reqFuel = 12.7 (see 2026-04-03 entry). Corrected chain: **12.7 × 265/425 = 7.9** (identical from first principles: 1839 cc/4 cyl/AFR 14.7/425 cc). Cross-checked against a real running turbo-Miata tune (`matt_tune_v2_9_7_26.msq`): battVCorMode **Open Time only** (Whole PW was adding ~12% at cranking voltage), crankingEnrichTaper **0.1 s** (3.0 s was stacking enrichment across every catch and drowning it). Empirical support: 7.0 was the only value that ever caught/revved.
- **Result/Evidence:** Verified live in `CurrentTune.msq` (07-11 07:35): reqFuel 7.9, Open Time only, taper 0.1, CrankAng 10, crank-wall cells intact.
- **Verdict:** Applied and loaded; outcome pending a clean cranking test.

## 2026-07-11 — TAS-vs-AAS correction; "air starvation can't fire" reasoning corrected
- **Change/Action:** Claude proposed opening the throttle stop screw for base air. User challenged; FSM research overturned it: the **TAS (throttle adjust screw) is factory-set and must not be adjusted** (FSM 01-10-17) — the designed base-air adjuster is the **AAS (air adjusting screw)** on the throttle body; NBs idling with the IACV unplugged idle on AAS + thermo-wax valve air. Also corrected the physics: **67 kPa cranking charge is ~2× a warm idle's charge mass — plenty to fire**; deep cranking vacuum certifies good sealing rather than preventing combustion.
- **Verdict:** TAS advice retracted. "Closed throttle can't fire purely from lack of air mass" REFUTED — the closed-throttle no-fire cause is back open (mixture at light-off vs. idle-air, now with corrected fuel chain in play).

## 2026-07-11 (morning) — First cranks on the corrected fuel chain (pending analysis)
- **Change/Action:** Cranks logged at 07:23 and 07:37 with reqFuel 7.9 chain live.
- **Result/Evidence:** `2026-07-11_07.23.06`: brief blips (~14 rows >500 RPM, one RPM spike artifact), MAP min 65, **battery sagged to 6.7 V again**, flood-clears used (TPS 100). `2026-07-11_07.37.33`: max 622 RPM, 3 rows >500, MAP min 70, battery min 7.1 V. No sustained catch.
- **Verdict:** PENDING — battery sag is back and invalidates the test; needs charged battery + dry plugs + ≤5 s cranks before the 7.9 chain can be judged.

## 2026-07-11 (midday) — Plug read confirms rich → idle-region lean-out (`TurboExo_idleleanout_2026-07-11.msq`, LOADED)
- **Change/Action:** Pulled plugs after the morning cranks: **cyl #2 black/sooty on a *fresh* plug**, #1 barely sooty, #3/#4 fairly clean; smells rich. Two edits to `CurrentTune.msq`: (1) **reqFuel 7.9 → 7.1**; (2) reverted the six 07-10 crank-VE/crank-wall cells to `VEfix` (07-09) values — 500 RPM col loads 40/46/50/60 kPa → 41/45/47/46, 700 RPM col loads 50/60 → 50/49. Kept battVCorMode "Open Time only", taper 0.1 s, CrankAng 10°. Pre-change state saved (`restorePoints/TurboExo_2026-07-11_pre-idleleanout.msq`).
- **Why/Hypothesis:** 7.9 used the **wrong-year injector** — 265cc is the 01–05 purple / 94–97 tan, not this car's **238cc "red" (Denso 195500-3310)**. Correct: **12.7 × 238/425 ≈ 7.1** (pressure cancels; = the empirical 7.0 that ran on 07-09). The 07-10 VE forcing also created an **"idle-vacuum trap"**: at the proven idle point (500 rpm × 53 kPa) VE=100 commands ~**2.25×** the fuel, so it floods and can't lean to idle — it stays pinned near-atmospheric (MAP 93–98) instead of pulling vacuum like the 07-09 run (which pulled to 53 kPa, idled at PW ≈ 2.5 ms).
- **Result/Evidence:** Judged from **delivered fuel (PW), not AFR** (still == Target in 100% of firing rows — the Spartan warmup echo). Crank-VE/crank-wall cells = **~80%** of the idle over-fuel, reqFuel = the other **~20%**; the taper + battVCor edits were slightly *leaning*, not the cause. **Cyl #2 is hardware, not tune**: PW1 = PW2 to 0.000 ms every log, and #2 shares its injector driver **and** wasted-spark coil with the clean #3 → per-cylinder (isolate by swapping injector #2 ↔ #1). Verified live: `CurrentTune.msq` reqFuel 7.1, six cells = VEfix. Project is now git + LFS (`github.com/grossadamm/turboexo`) with `AGENTS.md` / `docs/REFERENCE.md` / `STATUS.md` / `scripts/analyze_log.py`.
- **Verdict:** Applied and loaded; **supersedes 7.9 (07-11 anchor audit) and 8.5 (07-09)** — both too rich. PENDING a clean test on a charged battery. Global lean-out addresses the rich mixture; **cyl #2 is a separate hardware fault** leaning cannot fix.

---

## Current state / open items (as of 2026-07-11)

**Loaded tune:** `CurrentTune.msq` = reqFuel 7.1, battVCorMode "Open Time only", crankingEnrichTaper 0.1 s, CrankAng 10°, factory-transplant VE with the 07-10 crank-VE/crank-wall cells reverted to VEfix (idle region back to the 07-09 shape). Snapshot: `TurboExo_idleleanout_2026-07-11.msq`. (Living status also in `STATUS.md`.)

**Verified good:** trigger/full sync, spark all cylinders, base timing (yellow ≈6° vs commanded 5°), MAP plumbing + sensor, fuel pressure, injectors pulse, grounds/ECU power (when battery charged), IgInv "Going Low", idle PWM config (matches factory).

**Open items:**
1. **Battery discipline** — sagging to 6.7–7.1 V again on 07-11 cranks; charge/jump-pack before every session, ≤5 s cranks, dry plugs.
2. **Clean closed-throttle test of the 7.1 lean-out** — if it catches, hold 1500–2000 RPM (first raise `engineProtectMaxRPM` off 1500 — currently a fuel+spark cut right at the target), watch oil pressure not RPM.
3. **IACV airflow** — powered but not proven flowing: buzz-while-cranking test, **`iacPWMdir` polarity** (`iacStepperInv` is a no-op — this is a PWM valve, not a stepper), stuck/carboned valve; AAS (not TAS) is the base-air adjuster if needed.
4. **Wideband usable only after ~15 s+ of running exhaust heat** (Spartan warmup sequencer); optional ego_sdelay=0 for log clarity. Brown wire = heater-status (2 V = valid) — candidate spare analog input.
5. **Cyl #2 rich (hardware, not tune)** — fouls a *fresh* plug while #3 (same injector driver + coil) stays clean; isolate by swapping injector #2 ↔ #1 (soot follows injector = leaking/over-flow; stays with cylinder = coil tower/wire or compression).
6. After NA idle/road tuning: regenerate boost VE rows (current 120–200 kPa rows are placeholders), re-run `patch_commissioning_settings.py`, fit oil-pressure sender, knock conditioner before any knock features.

## Key reference values

| Item | Value | Note |
|---|---|---|
| Healthy cranking MAP (closed throttle) | **80–95 kPa** | observed 62–71 = air path deficit; 77–84 (June) was normal, not a leak |
| Warm idle MAP (healthy) | **28–37 kPa** | >~40–45 kPa warm = suspect vacuum leak |
| reqFuel (correct derivation) | **12.7 × 238/425 ≈ 7.1 ms** | 1999 stock = 238cc "red" (Denso 195500-3310), NOT 265cc (that's 01–05 purple / 94–97 tan) — the 265→7.9 and 14.7×238/424→8.5 chains were both too rich. Pressure cancels; matches the empirical 7.0 that ran |
| Injectors | RX-8 yellows ~424 cc/min @ 43.5 psi | "450cc" is a marketing/higher-pressure figure |
| Spark plugs | **NGK BKR7E (#4644), gap 0.030"** | 2 steps colder for turbo; not BKR7E-11 |
| IACV (NB 1.8) | **8.7–10.5 Ω** coil, PWM **~500 Hz**, 2-wire low-side, fails closed | early generic research said 11–13 Ω; FSM spec is 8.7–10.5 |
| Ignition polarity | IgInv = **"Going Low"** | never "Going High" (holds coils energized) |
| Flood clear | TPS > 90% while cranking → PW 0 | tpsflood=90 |
| AFR cal | 0 V = 10.0, 5 V = 20.0 AFR | Spartan warmup artifacts: 13.2 (1.66 V) and ~16.5 plateaus |
| Wasted spark / injector pairing | 1+4 & 2+3 (both) | a banked electrical fault cannot produce a 1&2-only pattern |
| ECU link | /dev/cu.usbmodem101 @115200 | data cable required (charge-only cables fail silently) |
| Log tooling | `npx mlg-converter --format=csv <file>.mlg` | semicolon CSV in DataLogs/ |
