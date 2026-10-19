# TurboExo Experiment Log — no-start → first-idle campaign

1999 Miata NB1 1.8 (BP-4W), TD04L-13T external turbo, Speeduino UA4C (fw 202501), speed-density, TunerStudio dash on a Pi. As of 2026-09-28: **stock 238 cc red injectors, Semi-Sequential injection, four Toyota/Denso 673-1300 / 90919-02239 COPs; saved ignition mode Wasted COP**. Earlier entries describe the previous yellow injectors and wasted-spark coils. Engine ran fine before the build; the build was **rewire + external turbo only** (internals known-good).

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

## 2026-07-12 — Rev-cap raised, taper restored, battery reinterpreted → still only motoring (adversarial review)
- **Change/Action:** `engineProtectMaxRPM` 1500 → 3000 (07-11), then `crankingEnrichTaper` restored **0.1 → 3.0 s** to match the 07-09 catch. On the car the operator pushed further: taper → **5.0 s**, `crankRPM` 400 → **230** (running mode sooner), `tpsflood` 90 → **60**.
- **Why/Hypothesis:** Battery reinterpreted — cranking ~10 V is workable, **not** the start blocker (07-09 cranked at ~10.9 V too; its 13–14 V appeared only *after* it caught = alternator). Restoring the taper (07-09 ran on 3.0 s; 0.1 s had starved the post-catch climb) should reproduce the 07-09 climb.
- **Result/Evidence:** Logs `2026-07-12_10.41.28` and `15.25–15.30`: weak catches to ~**500 rpm, dead-steady, 0.3–0.9 s, then die**; never charged. **Adversarial log review** proved the closed-throttle "catch" is **starter motoring, not combustion**: RPM 443 → 0 in one sample the instant the starter released, MAP 64 explained by piston pumping (not idle vacuum), the PW taper is speed-density math. The 1010/893 peaks were a battery-crash spike / WOT flood-clear blip. More taper fuel bought hold time but **no climb**.
- **Verdict:** Retractions kept for the record — "lean-out validated" and "it held" were **false**; "more fuel didn't help → it's air" was an **unsupported jump** (logs can't measure mixture [AFR echo] or separate weak firing from cranking). Cause of "won't climb" is **undetermined from logs**; needs discriminating tests (throttle-air → does it climb; plug read; does #2 fire).

## 2026-07-19 — Swapped to OEM injectors → back to the known-good factory fuel baseline
- **Change/Action:** **Removed the RX-8 yellows, installed OEM stock injectors.** Tune set to the factory fuel baseline: **reqFuel 7.1 → 12.7** (factory value *for these injectors*), `injOpen` 0.9 → 1.0, `primePulse` ~4 → ~30 ms, `battVCorMode` → "Whole PW", `fpPrime` 2 → 5 s, `primingDelay` 1 → 3 s, `engineProtectMaxRPM` → 4000. VE unchanged (factory-transplant).
- **Why/Hypothesis:** Eliminate the yellow-injector unknowns in one move — uncertain dead-time, flow, and the #2 fouling — by returning to the injector + fuel config the engine ran on for years. **reqFuel 12.7 is correct for OEM injectors** and supersedes the 7.1 derivation (which was for the yellows); the larger PW in ms is expected for smaller injectors (same fuel mass, longer pulse), not "rich."
- **Result/Evidence:** `2026-07-19_12.24.20` (113 s): revs to **893 rpm on a WOT (TPS 100) blip** (real combustion, held ~0.5 s, bogged to 327/PW 16 first), mean 526, MAP mostly 94–99, **no idle, never charged**. eff.fuel in ms looks large but is mass-appropriate for the smaller injectors.
- **Verdict:** Fuel is now at the **known-good factory baseline** (OEM injectors + reqFuel 12.7 + factory-transplant VE) → **fuel is largely off the table.** Persistent no-idle now points to the **non-fuel** side: idle **air** (IACV / base-air / vacuum leak) and **ignition**. **#2 is now a clean re-test** — new injectors in, so re-read plugs: clean = the yellow #2 injector was the fouler; still fouled = #2 spark/compression.

## 2026-07-19 (PM) — Red-team correction, then IT RAN (log cut off — pending push)
- **Change/Action:** (1) Red-teamed the four-lens no-start synthesis. (2) **The engine RAN** — but the datalog was **cut off mid-run when the ECU↔laptop USB link dropped** (the ECU keeps running the engine; the `.mlg` is a partial and is **not yet pushed**).
- **Red-team correction (verified against the logs):** my "everything log-visible matches 07-09, so the cause is invisible → fouled plugs" premise was **false**. Cranking power is *visibly* worse on 07-19 — **9.5 V / 231 rpm, never charged** vs 07-09's **10.9 V / 260 rpm, charged to 13.6 V**. So **"fouled plugs" is retracted** (also a documented non-fix — plugs cleaned/replaced ~5×). The four lenses are **not independent**: all read *commands* (advance, PW, IAC duty); none can see delivered fuel, per-cylinder firing, spark energy, or compression. Revised likely causes: **cranking power** (visible) + the **untested injector R&R** (delivered ≠ commanded, or a mis-seated injector seal = small leak). Two red-team over-reaches I did **not** accept: the 893 WOT burst does not refute fouled plugs (carbon fouling misfires at low load, clears at WOT), and MAP-high is better explained by open throttle + not-sustaining than a leak (cranking MAP 75 = decent vacuum).
- **Result/Evidence:** IT RAN (specifics pending the truncated log). The red-team's isolation test (hold ≥12.5 V under crank on the **same** plugs + ~12% throttle) may be exactly what got there — TBD from the log + the operator's account of what changed.
- **Verdict:** **Breakthrough — it ran.** PENDING the pushed partial log to characterize it: did it pull vacuum / charge / sustain, and what changed (battery / plugs / throttle)? That confirms or refutes the cranking-power hypothesis.

## 2026-07-25 — JUMPED FROM AN IDLING CAR → sustained running, real (lean) AFR, closed-throttle idle
- **Change/Action:** Ran a series of attempts with the car **jump-connected to a second, idling car** (steady ~13.6 V system). Logs `2026-07-25_09.01`–`09.33` (OEM injectors + reqFuel 12.7 baseline, unchanged).
- **Why/Hypothesis:** Hold the electrical system up during crank+run — strong spark/pump, and keep the Spartan wideband powered so it stops rebooting into its sequencer artifact.
- **Result/Evidence — breakthrough on two fronts:**
  - **It RAN long and idled.** `09.17.01` ran **379 s**, revved to **2230**, and held **closed-throttle idle** (TPS<5) for 4182 rows at ~600–1700 RPM (mean **934**), MAP down to **38 kPa** (real vacuum). `09.28.44` revved to **3153**, `09.33.18` to 2651. Voltage held **13.6 V while firing** (vs 10–11 unjumped) — confirms the jump, and that the car's own **alternator still isn't the source** (charge came from the donor).
  - **The wideband echo BROKE — AFR is now real data.** With stable power the Spartan stayed alive: AFR==Target dropped from 100% to **4–15%** in the long runs. And it reads **very lean: ~17.6–19.7 at idle** (near free-air). So the running mixture is now measurable, and it's **LEAN at idle**, not rich. eff.fuel collapsed to ~2 ms mean.
- **Verdict:** **Biggest step yet — sustained run + closed-throttle idle + usable AFR, all unlocked by holding voltage.** Reframes the campaign: no longer "won't run," now "runs lean at idle." Two follow-ups: (1) confirm the ~19 AFR is genuine lean vs sensor-not-fully-lit before adding fuel — but echo-break + movement says real; (2) the car's own alternator not charging is a real, separate defect (belt/exciter/wiring) to fix so it doesn't need a jump. Idle-air blocker appears **resolved** (it held closed-throttle idle) — was likely voltage-starved spark/valve, not a dead IACV.

---

## Historical state / open items (2026-07-25; superseded)

This section preserves the July working assumptions, including conclusions subsequently questioned. Use `STATUS.md` and the September 25 entry below for current hardware, evidence, and next tests. In particular, the old spark/timing checks do not verify the new COP installation, and breaking the AFR/Target echo alone does not establish a warmed, valid wideband reading.

**Loaded tune:** `CurrentTune.msq` (07-19) = **OEM injectors**, reqFuel **12.7** (factory value for OEM inj), injOpen 1.0, battVCorMode "Whole PW", crankingEnrichTaper 5.0 s, primePulse ~30 ms, CrankAng 10°, `engineProtectMaxRPM` 4000, crankRPM 230, tpsflood 60, factory-transplant VE. Snapshot: `restorePoints/TurboExo_2026-07-19_12.23.39.msq`. (Living status in `STATUS.md`.)

**Verified good:** trigger/full sync, spark all cylinders, base timing (yellow ≈6° vs commanded 5°), MAP plumbing + sensor, fuel pressure, injectors pulse, grounds/ECU power (when battery charged), IgInv "Going Low", idle PWM config (matches factory).

**Open items:**
1. **Battery discipline** — sagging to 6.7–7.1 V again on 07-11 cranks; charge/jump-pack before every session, ≤5 s cranks, dry plugs.
2. **Get a with-throttle catch on the OEM/factory fuel baseline** (reqFuel 12.7) — 07-19 revved to 893 only on a WOT blip. Reproduce the 07-09-style catch at ~10–15% throttle (rev cap is 4000, so let it climb); closed-throttle idle is the separate air problem.
3. **IACV airflow** — powered but not proven flowing: buzz-while-cranking test, **`iacPWMdir` polarity** (`iacStepperInv` is a no-op — this is a PWM valve, not a stepper), stuck/carboned valve; AAS (not TAS) is the base-air adjuster if needed.
4. **Wideband usable only after ~15 s+ of running exhaust heat** (Spartan warmup sequencer); optional ego_sdelay=0 for log clarity. Brown wire = heater-status (2 V = valid) — candidate spare analog input.
5. **Cyl #2 — now a clean re-test.** All injectors swapped to OEM (07-19), so re-read plugs after a run: #2 clean = the yellow #2 injector was the fouler; #2 still fouled = its spark path / compression (not fuel).
6. After NA idle/road tuning: regenerate boost VE rows (current 120–200 kPa rows are placeholders), re-run `patch_commissioning_settings.py`, fit oil-pressure sender, knock conditioner before any knock features.

## Historical July reference values

| Item | Value | Note |
|---|---|---|
| Healthy cranking MAP (closed throttle) | **80–95 kPa** | observed 62–71 = air path deficit; 77–84 (June) was normal, not a leak |
| Warm idle MAP (healthy) | **28–37 kPa** | >~40–45 kPa warm = suspect vacuum leak |
| reqFuel | **12.7 ms (OEM injectors, 07-19)** | Now on OEM stock injectors → factory 12.7 is correct. The **7.1** derivation (12.7 × 238/425) was for the RX-8 yellows, now removed; 265→7.9 and →8.5 chains were both too rich for the yellows |
| Injectors | **OEM stock (238 cc red), as of 07-19** | swapped back from RX-8 yellows (~424 cc) to eliminate the yellow unknowns for commissioning; yellows go back for boost later |
| Spark plugs | **NGK BKR7E (#4644), gap 0.030"** | 2 steps colder for turbo; not BKR7E-11 |
| IACV (NB 1.8) | **8.7–10.5 Ω** coil, PWM **~500 Hz**, 2-wire low-side, fails closed | early generic research said 11–13 Ω; FSM spec is 8.7–10.5 |
| Ignition polarity | IgInv = **"Going Low"** | never "Going High" (holds coils energized) |
| Flood clear | TPS > 60% while cranking → PW 0 | tpsflood=60 (was 90) |
| AFR cal | 0 V = 10.0, 5 V = 20.0 AFR | Spartan warmup artifacts: 13.2 (1.66 V) and ~16.5 plateaus |
| Historical wasted spark / injector pairing | 1+4 & 2+3 (both) | Applicable before COP conversion; ignition is now sequential, while injection remains paired |
| ECU link | /dev/cu.usbmodem101 @115200 | data cable required (charge-only cables fail silently) |
| Log tooling | `npx mlg-converter --format=csv <file>.mlg` | semicolon CSV in DataLogs/ |

## 2026-09-25 — COP conversion complete; new battery; crank/no-start remains unresolved

- **Change/Action:** Completed four-coil Toyota/Denso **673-1300 / 90919-02239** conversion. Sequential ignition wiring follows firing order: **IGN1 → cylinder 1, IGN2 → 3, IGN3 → 4, IGN4 → 2**. User reports **strong spark from all four coils in hardware output testing**. Stock **238 cc red injectors remain paired**; user reports the injectors were cleaned and bench-tested good. A new battery was installed between the first and second logs below.
- **Tune recovery:** The TunerStudio/controller difference report exposed an old **6.9 ms reqFuel** configuration while stock injectors were installed. The session found that state in the saved tune and restored the stock-injector baseline using `restorePoints/TurboExo_2026-08-29_19.22.11.msq`. Subsequent saved-file verification showed **reqFuel 12.7 ms, injOpen 1.0 ms**, restored VE/priming/IAC baseline, and engine protection maximum **4000 rpm**. File verification is not proof of the ECU's burned contents; burn, power-cycle, and readback remain distinct operations.
- **Ignition settings verified in the saved file:** Sequential, Going Low, cranking/running dwell **4.0/2.5 ms**, dwell map No, overdwell protection On/10 ms, dwell error correction Off, Miata 99–05 trigger, rising edges, trigger angle 0°, cranking advance 10°, cranking threshold 250 rpm, and **Fix cranking timing with trigger On**. Injection stays Paired; flood-clear threshold is 60% TPS. The dwell values are provisional starting recommendations, not a verified Denso dwell specification.
- **Correction/retraction:** Earlier advice in this session to turn crank timing lock Off was withdrawn. The [official Speeduino Miata 99–05 decoder guide](https://wiki.speeduino.com/en/decoders/Miata_99) recommends enabling it. Review of firmware 202501.7 showed extended scheduled cranking dwell, but a trigger tooth can terminate charge earlier; the extended schedule does **not** establish four times the physical dwell. The earlier simple output-number-to-cylinder-number sequential mapping was also wrong; use the firing-order mapping above.

### Recorded attempts

Raw `.mlg` files and converted `.csv` files are in `DataLogs/`.

| Log | Measured result | Interpretation / limits |
|---|---|---|
| `2026-09-25_10.44.47` — Pi, old battery | About 9.5 s cranking captured, starting mid-attempt; max 223 rpm; mostly 8.9–9.3 V; full sync, zero losses; commanded dwell ~4.2 ms; Gbaro 100% | No sustained catch. TPS above 60% cut injection for the first ~2.5 s; fuel then resumed around 17–18 ms. Low cranking voltage was measured, but was not established as the sole no-start cause. |
| `2026-09-25_13.16.22` — Pi, new battery | Two cranks ~6.5 and 7.6 s; max 251 rpm; mostly 10.3–10.6 V; full sync, zero losses; paired PW around 16 ms; **commanded dwell and Gbaro logged as zero** | New battery improved voltage and speed without a clear catch. Barometric **pressure** remained 99 kPa. Zero Gbaro conflicts with the saved 100% correction table and substantial fuel commands; actual zero coil charge is not proven. |
| `2026-09-25_14.33.35` — desktop/local | Coherent crank sections at 74.678–79.937 s and 93.561–97.076 s; max 253 rpm; mostly 10.5–10.6 V; full sync, zero losses; **dwell mostly 4.12 ms, Gbaro 100%**; matching injector channels generally 15–16 ms; no flood-clear cuts | No clear catch. The prior Pi zero readings were not reproduced. A telemetry/data-path issue is plausible, but its exact source is unresolved. |

- **Sensor review:** The newest local cranking data showed MAP 90–98 kPa, baro 99 kPa, IAT 59°F, and coolant 84–86°F. No reviewed sensor value explained the earlier zero dwell/Gbaro combination. Nonzero commanded dwell and PW still do not prove delivered spark or fuel.
- **Measured-dwell caveat:** The local log's `Dwell _Measured` reaches roughly 16.5 ms. In the reviewed firmware, scheduler completion supplies that elapsed-time measurement, while crank-lock tooth-triggered shutdown can end physical charge earlier without updating it. Do not interpret this log value as a direct electrical measurement of coil charge time. Source review: [main ignition scheduling](https://github.com/speeduino/speeduino/blob/202501.7/speeduino/speeduino.ino) and [timer/watchdog logic](https://github.com/speeduino/speeduino/blob/202501.7/speeduino/timers.cpp).
- **Log tooling caveat:** The newest local log resets its timestamp near the end and has out-of-order initial timestamps. The analyzer's negative overall duration is invalid; the two crank sections above are internally coherent. Existing analyzer effective-fuel estimates use the old 0.9 ms injector-opening assumption; current stock-injector saved baseline is 1.0 ms.
- **Wideband/status:** AFR is not a trustworthy mixture basis for these attempts. Calibration-like plateaus and AFR/Target echoing remain present; echoing alone does not establish heater state, and breaking the echo does not establish valid mixture. Aux0 is configured Analog_local on **A8 / UA4C INP1** and was renamed `WideBandStatus`; some logs retain the Aux0 label. Observed ~93/402/604 counts correspond to ~0.45/1.96/2.95 V at a nominal 5 V reference. Exact controller model/status-output interpretation remains unresolved; earlier blanket "2 V means ready" advice must not be applied without verification.
- **Logging operations:** Live Pi inspection found automatic logging disabled. Both Pi logs were manually started, stopped, and downloaded; the latest attempt was logged locally. Historical claims that Pi logging is automatically armed are superseded by that inspection.
- **Verdict / next discriminating test:** **COP installation and output-test spark are complete; crank/no-start cause remains undetermined.** Verify spark during an actual brief fuel-disabled crank, then verify timing near 10° BTDC with a timing light. Output testing does not prove cranking spark or correct timing. The pre-conversion timing check cannot certify the new ignition installation. Keep the previous sustained July running and hot-idle issue as history, not as proof of today's cause. No fuel change is justified solely by these logs.

## 2026-09-25 (PM) — Paired injection was feeding only cylinders 1 and 2; Semi-Sequential fixes fuel; July idle was a two-cylinder run

- **Change/Action:** `injLayout` **Paired → Semi-Sequential** (pairing 1+4 & 2+3), saved and burned 18:04. Earlier in the afternoon `crankRPM` 250 → 300 (16:34). No other tune change; VE and advance tables verified identical to `TurboExo_VEfix_2026-07-09.msq` in the idle region and to the 07-19 baseline everywhere.
- **Why/Hypothesis:** The injector harness has **four individually wired injectors** (INJ1→cyl 1, INJ2→cyl 2, INJ3→cyl 3, INJ4→cyl 4). In firmware 202501.7, 4-cylinder **Paired drives pins INJ1 and INJ2 only** (`init.cpp` INJ_PAIRED case: schedule 1 → `openInjector1`, schedule 2 → `openInjector2`, `maxInjOutputs = 2`). Cylinders 3 and 4 therefore never received fuel. Plug read before the change: **1 and 2 wet, 3 and 4 dry** — the wet pair crosses the injector pairing and matches the pin assignment. Semi-Sequential drives INJ1+INJ4 from schedule 1 and INJ2+INJ3 from schedule 2 with the same pulse-width math as Paired (`init.cpp` INJ_SEMISEQUENTIAL case), so reqFuel 12.7 and all July PW references still apply. Logged `PW3`/`PW4` stay 0.0 in Semi-Sequential by design (`speeduino.ino`: PW3/PW4 zeroed when `maxInjOutputs < 3`); they say nothing about whether INJ3/INJ4 fire.
- **Result/Evidence:**
  - After the burn, **all four plugs wet** (first time ever observed). Injector output tests on all four channels pass. Fuel now reaches every cylinder.
  - **Retroactive finding:** every July log (including `2026-07-25_09.17.01`, the 379 s idle) shows `PW3 = PW4 = 0` under Paired. If the harness was already individually wired then, **the July idle ran on cylinders 1 and 2 only**, which also explains the 17.6–19.7 "lean" wideband reading (two unfueled cylinders pumping air). `[inference: depends on when the harness was rewired]`
  - Catch behaviour after the change is unchanged in shape: 18.16.42 / 18.21.27 / 18.23.46 catch 4 / 21 / 11 times, peak 647–710 rpm, longest run-mode stint 1.4 s at 33% throttle (430 → 710 rpm, battery rising 11.1 → 12.5 V = starter unloading = real torque), dying the row the throttle moved and accel enrichment put PW at 20.2 ms. 16.15.10 (before the change, plugs freshly cleaned, cylinders 1+2 only) ran 3.5 s at 80% throttle crawling 341 → 630 rpm, MAP pinned at 98.
  - Afternoon logs 15.00–16.38 were taken with the **intake off and hoses disconnected** (spark/fuel isolation work), so their cranking MAP of 90–98 kPa is not comparable to July's 73–83.
- **Firmware facts established from source (202501.7, Miata 99-05 decoder):** with `ignCranklock` On and RPM < crankRPM+30, the decoder ends coil charge on teeth 1/5 (coils 1+3) and 3/7 (coils 2+4) at a fixed 10° BTDC; in Sequential mode each coil is still charged on its own 720° schedule, so the tooth only ends a charge already in progress. **Crank-lock catches therefore prove cam phase and the IGN→cylinder mapping are correct.** In run mode RPM is computed once per 720° (cam speed), so a logged RPM value held constant is one or more cycles at that speed and the value freezes until stall timeout; "catch dies in one cycle" cannot be resolved from the log.
- **Verdict:** **Fuel side is now correct for the first time.** Wet plugs on all four with catches that crawl at 500–700 rpm under 30–80% throttle means fuel arrives and does not burn well in any cylinder; a single-cylinder fault is excluded. The only system changed for the worse since the July two-cylinder idle is ignition (two wasted-spark coils at 6.0/3.0 ms → four Denso 90919-02239 COPs at 4.0/2.5 ms, Sequential). **Next single-lever test:** `crankRPM` 300 → 800 to hold crank-lock spark through the catch, one crank ≤5 s, throttle held under 60% (flood clear applies across the whole crank regime; overdwell protection is off below crankRPM). Climbs through 800 → run-mode ignition path is the fault; restore crankRPM and raise `dwellrun` to 4.0 to split dwell from timing. Still crawls → handover exonerated; raise `dwellcrank`/`dwellrun` together, since the coils are the one unverified component in both regimes. Two independent agent reviews of this log set agreed on the fuel finding and on excluding sequential phase; they split on dwell-first vs crankRPM-first.

## 2026-09-28 — Warm idle established; crank threshold and closed-loop IAC staged

- **Evidence:** `2026-09-28_13.09.03.csv`: continuous running ~328 s, closed TPS ~233 s,
  no sync loss; tip-in bog present, transient AFR not conclusive. `13.29.24.csv`:
  ~16.9 s warm closed-throttle idle, 187–190°F, WUE 100%, median 1601 rpm / 32 kPa /
  AFR 12.1 versus 14.3 target / PW 1.893 ms, IAC settles 75%. Initial timestamp is
  discontinuous; excluded from duration. No throttle opening is captured in warm log.
- **User direction:** Move from no-start diagnosis to idle/run tuning. Lower crankRPM
  800→300 and add closed-loop IAC. This explicitly authorizes both settings together;
  keep fuel/ignition unchanged. User identifies release flutter after the bog, with
  bypass installed. No recorded positive manifold boost, no pre-throttle sensor.
- **Change:** Snapshot `TurboExo_pre_closedloop_2026-09-28_142246.msq`. Updated `CurrentTune.msq` and staged `TurboExo_closedloop_2026-09-28_142246.msq`:
  PWM Closed+Open loop; 65–90% limits; P/I/D 0.0625/0.03125/0; TPS reset 2%; RPM reset
  hysteresis 1000; targets [1200,1200,1200,1150,1100,1050,1000,1000,1000,1000] on existing
  coolant bins. Existing OL curve retained as feedforward. crankRPM=300.
- **Why:** Pure PWM CL lacks the combined-mode TPS/RPM integral-reset behavior. Existing
  zero limits and P=2/I=0 were unsuitable to simply enable. At 500 Hz and raw gains2/1,
  a 600-rpm error initially gives ~7.5 duty points P and ~3.75 points/s I correction.
  65% floor and 90% ceiling are deliberately bounded, unverified commissioning limits.
- **Source review:** Speeduino 202501.7 `idle.cpp` PWM_OLCL and integerPID in
  `src/PID_v1/PID_v1.cpp`; local INI scaling and restart requirements. Combined startup
  initializes integral from crank duty and can briefly hit ceiling when feedforward
  is added; the old PWM taper does not apply. Independent reviewer checked semantics.
- **Spartan correction:** Model is explicitly recorded as Spartan 3 OEM in checklist
  line36 and June12 entry, but later reference claims Spartan2. Prior analog 0/1/2 V
  readiness claims remain unverified. Current Spartan3 OEM pinout has no named analog
  heater-status output. Warm Aux0 high is supporting behavior, not verified readiness
  or accuracy. No wideband calibration changed.
- **Validation/result:** XML parsed; compared all constants against exact pre-edit
  snapshot: only the nine intended crank/IAC constants changed. Gains encode raw2/1,
  target table has ten values, staged file matches CurrentTune. No ECU connection,
  burn/readback or physical response validation performed. Open named staged file,
  burn, power-cycle, verify readback and log warm idle/return. **Outcome pending.**

## 2026-09-28 — COP hardware documentation made explicit

- **User confirmation:** The engine uses COPs, not the original Miata coils.
- **Documentation:** Updated AGENTS.md, STATUS.md, the reference rig/ignition sections,
  and this log's current-configuration header to name the four Toyota/Denso COPs,
  documented wiring, and saved Wasted COP mode. Distinguished hardware from ECU mode;
  retained prior Sequential/stock-coil observations as history. Replaced the obsolete
  shared-coil-tower diagnostic instruction. Current objective is idle/run calibration.
- **Validation:** Checked documentation against the September 25 conversion entry and
  saved sparkMode. Documentation only; no tune or ECU settings changed.

## 2026-09-28 — Non-OEM Spartan replacement confirmed; correct manual downloaded

- **User correction:** Original OEM module was replaced by a purchased non-OEM
  Spartan, including the separate status wire. Prior reliance on the OEM manual
  was wrong; the old model references do not identify the currently installed unit.
- **Sources:** Downloaded official Spartan 3 v2 (Jan21 2026) and legacy Spartan 3
  (Nov24 2023) manuals to `docs/manuals/`, with source URLs/hashes in README.
  V2 wiring table explicitly specifies brown heater status:0V waiting,1V heating,
  2V heat-up complete/heater closed loop. `GETNBMODE`:2 heater status,0 narrowband.
- **Remaining measurement question:** Warm Aux0 565–604 counts nominally corresponds
  to2.76–2.95V for a direct10-bit5VADC, not nominal2V. Verify input transfer or brown
  output voltage/configuration; do not translate ADC600 into ready solely by naming
  the channel. Analog status and CAN codes1/2/3 are different encodings.
- **Changes:** Updated current STATUS/reference and checklist model label. No tune,
  controller output configuration or calibration changed. Exact replacement
  hardware/firmware revision has not been read back.

## 2026-09-28 — Oil pressure input configured on INP2/A9 (saved, not burned)

- **User hardware:** 0–100 psi transducer, linear 0.5V=0psi / 2.5V=50psi /
  4.5V=100psi; user handles wiring and selected the other spare input, INP2/A9.
- **Change:** Snapshot `TurboExo_pre_oilpressure_2026-09-28_180624.msq`; enable native oil-pressure monitoring on A9 in
  CurrentTune.msq and `TurboExo_closedloop_oilpressure_2026-09-28_180624.msq`. Oil-pressure protection remains Off; no cut
  thresholds enabled. Existing staged crank/IAC edits preserved.
- **Calibration:** Firmware202501.7 `sensors.cpp:getOilPressure` maps ADC fullscale
  using oilPressureMin/Max; INI labels are Pressure at0V/5V. Exact sensor endpoints
  extrapolate to -12.5/112.5psi, but storage is integer psi. Saved -13/113psi gives
  nominal0.5V→-0.4(clamped0),2.5V→50,4.5V→100.4psi before ADC/integer/filter effects.
  Built-in0–100PSI preset(-3/103) is NOT correct for this supplied transfer curve.
- **Validation:** XML parsed; only oilPressureEnable/Pin/Min/Max changed; protection
  verifiedOff; staged file byte-identical to CurrentTune. No ECU burn/readback or
  sensor voltage/pressure verification. Enable and pin require power cycle per INI.

## 2026-09-28 — Current wiring notes consolidated

- **Change:** Added docs/WIRING.md for COP/injector output-to-cylinder assignments,
  Spartan replacement/status input INP1/A8, oil transducer INP2/A9 and its calibration.
  Explicitly distinguish hardware reported wired from newly assigned/staged oil input.
- Updated README/AGENTS/reference/checklist links and current assignments. Marked
  June boost/first-start settings historical to prevent reuse of stock-coil or yellow
  injector guidance. Documented charging confirmed without an external power source.
- **Validation:** Cross-checked A8/A9 against local UA4C schematic and four oil constants
  in CurrentTune; preserved unknown sensor supply/connector pinout, IAC harness cavity,
  and oil installation/readback status. Documentation only, no tune changes.

## 2026-09-28 18:11:45 — User fan-temperature save supersedes named staged tune

- **Change:** User saved fan-on temperature in TunerStudio. `CurrentTune.msq` now
  contains `fanSP=120.186°F` (UI displays 120°F), replacing 201.186°F. Hysteresis
  remains 7.2°F (UI displays 7°F).
- **Evidence:** CurrentTune bibliography and file timestamp show 18:11:45 PDT;
  `restorePoints/TurboExo_2026-09-28_18.11.45.msq` records “User Requested Save of
  Settings” and the same fan setting. Compared all constants with
  `TurboExo_closedloop_oilpressure_2026-09-28_180624.msq`: fanSP is the only change.
  CrankRPM 300, closed-loop IAC and A9 oil monitoring are preserved.
- **Verdict:** **CurrentTune.msq is the newest combined file.** The named 18:06
  copy retains the old 201.186°F fan threshold; loading it would revert this save.
  Earlier checks saw the prior save; the newly verified 18:11 save resolves the
  discrepancy. Saved file evidence does not confirm ECU burn or actual fan response.
- **Documentation:** Updated STATUS.md latest-file guidance and added a short
  file-routing section to AGENTS.md. No tune settings changed by this documentation edit.

## 2026-09-28 — Commit/handoff checkpoint

- Rechecked CurrentTune after TunerStudio's 18:16:50 save: all constants match the
  18:11:45 restore point, including 120.186°F fan-on and crank/IAC/oil setup.
- New `DataLogs/2026-09-28_18.17.07.mlg` exists but has not been converted or analyzed.
  Do not assume the staged closed-loop settings have been validated by this run.
- Commit scope: current tune, session documentation/manuals, four named tune
  snapshots, September 28 restore points and the two reviewed September 28 logs.
  Unrelated working changes and the new unreviewed log remain outside this checkpoint.


## 2026-09-28 evening — 18.17.07 analyzed; IAC at minimum, fan works, oil signal unverified

- **Action:** Confirmed checkpoint HEAD `13e15d9`; preserved existing uncommitted
  work. Converted newest local `DataLogs/2026-09-28_18.17.07.mlg` to semicolon CSV.
  Ran the existing analyzer and independently examined individual channels and
  coherent time segments. No tune changes or ECU operations.
- **Data quality:** Initial time-zero placeholder jumps to 40.297 s; occasional
  duplicate timestamps, no backward reset. Continuous RPM>400 from 45.030 to
  215.036 s (~170 s). Zero recorded sync losses. TPS exactly zero throughout;
  AE never exceeds 100%, so this log does not reproduce the throttle bog.
  Battery is normally 13.8–14.6 V after startup. At 214.840 s voltage falls to
  9.6 V while RPM still reads 1611, followed by RPM=0 at 215.107 s and about
  4 V afterward. Consistent with shutdown/supply loss, not proof of an idle stall.
- **Idle result:** IAC starts near its ceiling (89 logged), falls to 64 at
  66.306 s and stays there through the run. Firmware 202501.7 `idle.cpp` sets
  PID limits in timer ticks*4, shifts the result down, then truncates the logged
  percent. At AVR 500 Hz, 65% produces 81/125 ticks (64.8%), logged as 64;
  90% similarly logs 89. Thus floor/ceiling values match the saved limits.
  At 150–214.7 s: target1000, RPM median1555/range1373–1635, MAP median32,
  IAC64, battery median14.5 V. Requesting less duty has not achieved target;
  physical valve response/other air paths remain unverified. More PID gain
  cannot overcome an already saturated output. No automatic limit widening.
- **Temperature/fueling limits:** CLT84–136°F; WUE116% initially and106% at end.
  This is not fully warm idle. At150–214.7 s, indicated AFR median12.6 versus
  target14.3; PW median1.972 ms. No fuel edit justified from these readings.
  Existing analyzer effective-fuel output uses historical RX-8 yellow injector
  dead-time data and is not a validated effective-fuel estimate for current reds;
  its echo percentage also does not independently determine heater readiness.
- **Fans:** User explicitly confirms fans work. Logged fan command turns on at
  162.035 s with CLT120°F, matching the latest saved threshold. Median RPM in
  the10 s before/after is1580.5/1537; median voltage14.5 V in both windows.
  No stall on engagement. Fan stays commanded on until engine stop at136°F;
  no temperature-driven off cycle, so hysteresis/cooling capacity not established.
- **Oil anomaly:** Pressure14 psi before cranking, falling to0 by47.430 s and
  remaining0 throughout sustained running; returns to14 after shutdown.
  Actual oil pressure cannot be inferred reliably. Asked whether the sensor was
  fully connected during this run and whether an independent reading exists.
  Verify actual pressure before further sustained running, then wiring/supply/
  ground/input and ECU calibration/readback. Leave oil protection Off while its
  input is unverified. Firmware `sensors.cpp:getOilPressure` maps the analog
  input, filters and clamps it; the logged zero is not a raw voltage measurement.
- **Spartan:** Stable Aux0 approximately598 counts (nominal2.92 V for direct
  5 V/10-bit ADC) still does not reconcile with the manual's nominal2 V heater-
  ready output. Verify actual brown-wire voltage/input transfer and controller
  mode/revision. Heater readiness would still not certify AFR analog accuracy.
- **Saved tune validation:** All CurrentTune constants still match
  `restorePoints/TurboExo_2026-09-28_18.11.45.msq`. CurrentTune remains the combined
  baseline; older named staged copies would revert fan temperature. Observed
  controller behavior supports applied settings but is not complete burn/readback.
- **Verdict:** Sustained idle and fan operation confirmed; idle target not achieved,
  throttle bog not tested, oil measurement unresolved. Discuss findings and verify
  pressure/idle-air response before choosing another tune change.


## 2026-09-28 evening — Expected analog inputs documented; 18.21.44 analyzed

- **User request:** Document expected Spartan/UA4C input behavior, then inspect
  newest log. Added expected brown-wire0/1/2 V and nominal Aux0 0/205/409 table,
  electronics/heater grounding distinction, mode2 readback expectation, and
  UA4C vC5 JP7/JP8 circuit details to docs/WIRING.md. Added official hardware
  source links to docs/manuals/README.md. For driven voltage signals, recommend
  unbiased inputs (JP7/JP8 unbridged), explicitly a circuit-based recommendation,
  not a verified factory default or claim about the installed board. Actual
  revision/jumper positions remain unknown. No hardware or tune settings changed.
- **Newest log:** Converted18.21.44.mlg; coherent316.771–432.513 s=115.742 s.
  Initial isolated219.104 s row precedes97.667 s gap; seven duplicate timestamps.
  Existing analyzer was run, but its duration and historical injector-deadtime
  estimate were not adopted. Independent raw-channel analysis used for findings.
- **Idle:** IAC reaches64 at327.241 s. Stable350–398.581: target1000, RPM median
  1581/range1484–1649, MAP median32/range30–33, IAC64. Final427–432.513: RPM
  median1433.5/range1384–1522, MAP35, IAC64. Coolant136→162°F; WUE106→102%.
  No fully warm equilibrium. Floor quantization remains consistent with saved65%.
- **Throttle windows (log seconds):**
  -398.690–399.842: TPS max8%, RPM~1563→3069 at399.911; AE138% for two rows.
  -401.852–413.644: TPS max8%, RPM1641→1467 at402.246 then3490 at404.456;
   AE100% throughout. RPM already falling after previous release. During the
   brief dip MAP28→53 kPa, PW1.758→2.874 ms, indicated AFR13.4→19.2. At minimum,
   battery14.6 V, advance18°, dwell2.45 ms, no recorded sync loss. Transient
   hesitation present; lean mixture versus misfire remains unresolved.
  -415.246–417.847: TPS max16%, RPM1701→1660 briefly then4303 at417.646; AE100%.
  -421.115–423.380: TPS max16%, RPM1517→3815; AE100%.
  Releases show rich-indicating AFR dips (minimum10.5); no stall. Maximum MAP58 kPa,
  no positive manifold boost. Hard limiter/launch/boost-cut logged flags all0.
- **Fan/oil/status:** Fan1 throughout coherent recording; no new off-hysteresis
  evidence. Oil0–2 psi/median0 while running; initial isolated14psi row is not a
  valid stopped baseline. Sensor installation and independent actual pressure
  remain unverified. Aux0 early~380, settled~598: JP7 position and actual voltage
  need checking, not a revised readiness threshold. Late stable indicated AFR
  about12.6 versus target14.3 remains insufficient basis for a fuel change.
- **End/validation:** Ends running1387 rpm,14.5 V; zero sync losses. No shutdown
  captured. Compared all CurrentTune constants against18:11:45 restore point:
  no differences. Preserved unrelated work. Updated STATUS, wiring/manual notes
  and this history only, plus generated CSV. Discuss results before tune changes.

## 2026-09-28 evening — IAC unplugged finding; connected stall; fixed-duty test

- **User findings/authorization:** The IAC had been unplugged during the earlier
  high-idle testing. Reconnection lowered RPM and produced difficulty idling.
  User confirms19.09.47 ended in a stall and explicitly requests adjusting the
  connected valve rather than unplugging it. Intake manifold reported not fully
  seated; throttle-body idle screw tampered. Repair and exact screw identification
  remain unconfirmed. Earlier high-idle command-floor observations cannot be used
  as physical IAC response or proof of a valid duty range.
- **Run evidence:**19.09.47 coherent409.202–446.352 s, TPS0, CLT144–147°F,
  zero recorded sync losses. Initial439–648rpm at83–85% command; recovery to
  1151–1339rpm at73–76%; final stall1264→822→428→0 while command rises74→80→84.
  The65% floor was not reached. Voltage falls after RPM falls in the recorded
  sequence. About75% AFR/target echo among firing samples, no fuel inference.
  Oil signal now10–12psi running/0 stopped but independently unverified.
 19.09.10 contains only engine-off data; its first out-of-order row is excluded.
- **Baseline:** CurrentTune19:13:34 save includes the user's newer idleKI=0;
  only that constant differs from18:11:45 restore. Snapshot saved as
  `TurboExo_pre_IAC_fixed80_2026-09-28.msq`.
- **Change:** Created `TurboExo_IAC_fixed80_TEST_2026-09-28.msq` with only
  iacAlgorithm="PWM Open loop" and all ten iacOLPWMVal entries80%. CurrentTune
  left untouched. Crank duty83%, taper5s, frequency500Hz, Normal direction,
  one output, all other constants including I=0 preserved. Open loop uses83%
  during crank/pre-start and tapers to80% over5s; thereafter commands80%. Closed-
  loop limits/targets/PID do not operate in this mode. Idle-up/A/C adders off/zero.
- **Hypothesis:** A constant running command removes closed-loop duty changes
  from the next observation.80% is above the73–76% pre-stall command, within the
  recently observed range, and is a test point rather than an established cure.
  Known manifold sealing and bypass adjustment confound final calibration.
- **Validation/result/verdict:** Independent read-only firmware review checked
  `speeduino/idle.cpp`2025.01.7 open-loop branch and local INI. Parsed generated
  XML and compared every constant: exactly the two intended fields changed.
  Snapshot is byte-identical to baseline; CurrentTune bytes unchanged. Saved only;
  burn, power-cycle/readback and connected-valve result remain pending. Hold the
  mechanical screw setting steady during this comparison. Do not adopt flat80%
  as the permanent cold/warm idle curve.

## 2026-09-28 19:16 — Apply authorized IAC test to CurrentTune

- **User instruction:** Use CurrentTune.msq and snapshot accordingly.
- **Snapshot:** `TurboExo_pre_CurrentTune_IAC80_2026-09-28_191637.msq`, verified
  byte-identical to the latest19:13:34 TunerStudio save before editing. Its only
  constant difference from18:11:45 restore was the newer idleKI=0, preserved.
- **Change:** Applied PWM Open loop and all ten iacOLPWMVal entries80% directly
  to CurrentTune. Exactly those two constants changed; all others preserved.
- **Validation/result:** Parsed XML, compared every constant, verified snapshot
  bytes and CurrentTune byte equality with the named diagnostic. Saved only;
  ECU burn/readback and fixed-duty test result pending. Earlier separate-file
  loading recommendation superseded by CurrentTune as requested.

## 2026-09-28 19:19 — Fixed80 idle test still stalls

- **Result:** User reports engine died.19.17.57.mlg converted to CSV. CurrentTune
  now saved by TunerStudio19:17:56, every constant matches the staged80% test.
  Log commands83→80 during startup and holds80 from45.316–97.673 s while firing.
  This supports application of idle settings but is not full ECU readback.
- **Evidence:** TPS0 throughout. During50–95 s RPM median1244/range1014–1402,
  MAP median34kPa, battery median14.5V. End1364rpm at96.300 s,966 at96.791,
  699 at96.878,54 at97.743,0 at98.187. IAC stays80 through collapse, returns83
  only on cranking state. Voltage still14.5/14.4V as RPM initially collapses.
  No logged sync losses, errors, DFCO, hard-limiter, launch or boost-cut flags.
  Fan engaged41.051 s, well before stall. Coolant136–149°F, not fully warm.
- **Limits:** Initial placeholder/out-of-order row and nine duplicate timestamps;
  repeated699rpm/MAP36 samples restrict exact collapse timing. AFR rises from
  roughly12 to19.7 after RPM starts dropping; cannot distinguish fuel delivery
  loss versus misfire from this. PW commands persist, not proof of delivered
  fuel. Oil12–13psi running/0 stopped remains independently unverified.
- **Verdict/next discriminator:** Fixed duty did not cure the stall; commanded
  valve closing or PID action cannot explain this event. Physical valve behavior,
  fuel/spark delivery, known manifold sealing and tampered screw remain possible
  contributors. Asked whether screw/connector manipulation preceded the stall.
  No additional tune changes; CurrentTune remains fixed80 diagnostic.

## 2026-09-28 19:22 — Unplugged IAC comparison,19.20.07

- **User configuration:** IACV unplugged for latest log. Saved tune remains80%
  PWM Open loop; logged duty is only ECU command with connector removed.
- **Evidence:** Converted19.20.07.mlg. Excluded two time0 placeholder rows;
  coherent164.556–298.509 s. RPM>400 for128.676s and engine still running at end:
  1434rpm, MAP33kPa,14.5V, coolant178°F. TPS0 throughout. Late250–298.509s
  median1423rpm/range1286–1522, MAP median33kPa, battery14.5V; WUE100–101%.
  No recorded sync losses, hard-limiter or DFCO activation. No stall captured.
- **Comparison/verdict:** Connected80 test stopped after roughly58s; unplugged
  test continues for at least129s. Connected IAC valve/drive/airflow behavior is
  therefore more suspect, but duty direction, rest position and fault mechanism
  remain unproven. Different starting temperatures and known manifold/screw
  issues prevent treating these as perfectly controlled tests. Fixed80 analysis
  excluded commanded closure, not a physical IAC or driver fault. No tune edits.

## 2026-09-28 21:26 — Raise connected-IAC test duty80→85%

- **User direction/hypothesis:** Proceed with higher duty to test additional
  idle air. Previous80% steady command did not prevent a stall; stable RPM before
  that stall does not prove adequate airflow in every condition.
- **Snapshot:** `TurboExo_pre_IAC85_2026-09-28_212632.msq`, byte-identical to
  CurrentTune before editing. Latest saved source still19:17:56 TunerStudio save;
  compared against latest18:11:45 restore and preserved newer settings.
- **Change:** CurrentTune all ten iacOLPWMVal entries80→85%, single constant
  changed. PWM Open loop,500Hz,Normal,one output,crank83%,taper5s preserved.
  Crank-to-run now tapers83→85; fuel/ignition and all other constants preserved.
- **Validation/result:** XML parsed, every constant compared, backup verified.
  Saved on disk; burn/readback and connected85% test result pending.

## 2026-09-28 21:29 — Restore exact reference IAC running curve as requested

- **User instruction:** Use the researched reference89/75 curve first. The prior
  flat85% proposal did not match that request and is superseded.
- **Source:** Fresh raw GitHub fetch of Speeduino/Tunes main,
  Mazda/Miata_PNP99-00_SpeedyEFI.msq (UA4C99–00 base tune).
- **Snapshot/change:** Saved `TurboExo_pre_reference_IAC_2026-09-28_212925.msq`;
  changed CurrentTune iacOLPWMVal only to90,90,89,89,89,89,89,75,75,75.
  Temperature bins already matched reference exactly. Open-loop500Hz,Normal,
  one output,83% crank already matched. Retained current5s taper (reference6.2s)
  and every other constant; only the requested running curve transplanted.
- **Validation/result:** XML parse, exact reference curve/bin comparison, full
  constant diff, backup byte equality and final write verification passed.
  Saved only, ECU burn/readback and connected-valve outcome pending.

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


## 2026-10-04 — Restore VE map to today's 10:31 AM snapshot

User requested undoing the identified map changes. Snapshotted latest CurrentTune
as `TurboExo_pre_VE_rollback_2026-10-04_171421.msq`, then restored only `veTable` from
`restorePoints/TurboExo_2026-10-04_10.31.19.msq`: 18 increased cells reverted.
All other 806 constants preserved, including flood-clear TPS 80% and fan setpoint
190.386°F. XML parsing, complete constant comparison, exact reference VE match,
and snapshot/write byte verification passed. No running result yet.
Saved on disk only; reload CurrentTune in TunerStudio before burn/readback.
ECU application is unverified; this rollback does not establish a stall cause.


## 2026-10-04 — VE rollback restored after TunerStudio overwrite

At 17:16:30 TunerStudio saved the increased VE table back into CurrentTune.
The 17:15:20 reload logged zero bytes updated; subsequent burn was skipped because
no writes had occurred. Rollback was not applied by that sequence.
Restored the same 18 VE cells again, preserving every other constant, and created
`TurboExo_VE_rollback_2026-10-04_171644.msq` for explicit loading without relying on CurrentTune surviving autosave.
Backup: `TurboExo_pre_VE_rollback_retry_2026-10-04_171644.msq`. XML and full constant diff passed; only veTable changed.
Verified CurrentTune and named rollback are identical and match the 10:31 VE table.
ECU burn/readback remains pending. Load the named rollback file in TunerStudio.

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



## 2026-10-10 13:54 — Bluetooth ECU link through Pi and Dash Echo

- User authorized testing Pi Bluetooth, then using it as TSDash's ECU connection.
- Pi paired with Speeduino08203; native RFCOMM channel 1 returned F=`002` and
  Q=`speeduino 202501`. ECU USB was unplugged. This verifies a working module/UART
  path in this test, unlike earlier Mac direct-Bluetooth zero-byte results.
- Saved Pi project.properties.before-bluetooth-20261010 before changing TSDash
  to /dev/rfcomm0, 115200, Bluetooth Port=true. Enabled the repository-mirrored
  turboexo-bluetooth-serial.service; service startup and dashboard reconnection
  passed. No ECU calibration writes performed.
- Continuous Bluetooth telemetry observed. Mac on home Wi-Fi connected through
  192.168.1.134:21848 at 13:53:25 (Connected with Controller); page reads and
  matching checksums at 13:53:36. Pi TCP socket corroborates the client connection.
  Automatic logging remains enabled after restart. Raw ad hoc TCP F/Q probes
  timed out; actual TunerStudio Dash Echo connection subsequently succeeded.
- Keep Mac on home Wi-Fi during agent work; TurboExo hotspot lacks Internet.
  Hotspot endpoint remains 192.168.50.1:21848. Cold boot, sustained driving,
  connection recovery after ECU power cycling and actual tuning writes are not
  tested. Rollback details are in STATUS.md. USB and Mac Bluetooth root causes
  remain open; the new route bypasses them.

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


## 2026-10-10 — Revert cranking fuel reduction

User requested reverting the preceding cranking-enrichment reduction. Restored
crankingEnrichValues to 225/195/175/125% from the pre-reduction backup, preserving
all other current constants. Prior values: 225.0 195.0 175.0 125.0.
Backup: `TurboExo_pre_crankfuel_revert_2026-10-10_140616.msq`. Explicit load file: `TurboExo_crankfuel_reverted_2026-10-10_140616.msq`;
CurrentTune.msq matches. XML, full constant comparison and byte verification
passed. Saved on disk only; ECU burn/readback and start result unverified.
This supersedes the preceding reduction; no reason or test result was supplied.

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

## 2026-10-11 — Dark Bluetooth module; light backfeed found and disconnected

- **Trigger:** User asked whether settings reset after a TunerStudio difference
  dialog showed local 12.7 ms / Semi-Sequential versus controller-side 6.9 ms /
  Paired. Bluetooth had worked the previous day, including a recovery test.
- **Read-only evidence:** Pi saved tune retained 12.7 ms, Semi-Sequential and
  Wasted COP. Pi Bluetooth adapter was powered and pairing persisted, but the
  ECU link was disconnected; TSDash repeatedly timed out on F/Q identification.
  User observed a dark Bluetooth module LED. USB initially did not enumerate,
  then appeared as /dev/cu.usbmodem101. Direct queries returned F=002,
  Q=speeduino 202501 and S=Speeduino 2025.01.7. Reads using the project INI's
  page/telemetry definitions confirmed ECU reqFuel 12.7, injLayout 1
  (Semi-Sequential), sparkMode 2 (Wasted COP), RPM 0 and zero reported error
  flag/error byte. Battery reading was 3.4 V before key-on and 12.0 V after
  user-confirmed key-on; Bluetooth remained disconnected at that check.
- **Action/result:** User identified voltage backfeeding from a light and
  disconnected the light. Bluetooth improved; user then confirmed “all fixed.”
  No tune, firmware, or Pi configuration changes were made by this investigation.
- **Verdict and limits:** User-confirmed backfeed contributor and recovery.
  No independent post-fix telemetry verification, module supply measurement or
  documented exact light/circuit. Do not invent a diode fix or conclude module
  failure. USB response and ECU battery reading do not prove Bluetooth supply
  health. Zero telemetry errors do not constitute a complete hardware self-test.
  The three directly read settings showed no reset; the full tune and persistence
  across power cycles were not tested. The dialog's older values remain unexplained;
  stale/proxy data was a hypothesis, not a verified cause.
- **Learning:** Check actual ECU connectivity and power state before diagnosing
  tune loss. For a dark module, investigate supply/backfeeding and physical
  connections before replacing it or changing software. USB can be used for
  read-only diagnosis while Bluetooth remains the intended connection. For a
  complete power-off check, account for USB and accessory backfeed paths.

## 2026-10-17 — Verified output map, reset review and oil-pressure repair

- **User evidence:** individually hardware-tested injector AND ignition outputs
  1 -> cylinder 1, 2 -> 3, 3 -> 4, 4 -> 2. IAC remains physically unplugged.
  Starting fluid produced stumbling and an intake pop; this prioritizes measured
  cranking timing but does not establish the cause. No timing-light result supplied.
- **Reset review:** the 13:37:57 saved tune has 114 constant differences, including
  six added constants, versus the October 10 confirmed-running disk milestone.
  Core ignition and pairing match the verified wiring; cranking advance is 10.
  Fuel/startup tables changed substantially, including a flat 125% cranking curve.
  TPS endpoints are 27/185 and all seven ADC filters are zero. Fuel, ignition and
  AFR load axes now stop at 100 kPa. Closed-loop boost has zero targets and
  degenerate bins; it is not a calibrated boost setup. Firmware disables boost
  control for zero targets, so this does not establish an 85% solenoid command.
  The latest local 12.04.50 log predates the broad reset saves. Disk reset settings
  are not independently verified ECU readback or evidence of the reset's behavior.
- **Oil change requested and performed on disk:** oilPressurePin A8 -> A9;
  oilPressureMin -8 -> -13 psi; oilPressureMax 117 -> 113 psi; Auxin0pina A9 -> A8;
  PC alias AUXin00Alias OilPressure -> Aux0. This restores INP2/A9 native oil
  monitoring and INP1/A8 Spartan status. Monitoring stays On, protection Off.
  The user-specified 0.5/2.5/4.5 V transfer gives nominal 0/50/100.4 psi after
  clamping with the rounded endpoints, before ADC/filter/integer effects.
- **Preservation:** exact pre-edit backup
  `TurboExo_pre_oilpressure_fix_2026-10-17_134104.msq`; explicit corrected file
  `TurboExo_oilpressure_fixed_2026-10-17_134104.msq`. CurrentTune.msq matches.
  Source SHA-256: `7f0a32fafd32862130e4e69eb92d796b396c5040f8c34a8f9b7d24f367a99903`.
  Corrected SHA-256: `df06b0504af606b83f5b97ef9c1c85b15e7805037ec85a49b67c510f4f22b951`.
- **Validation/result:** XML parses; exact comparison confirms only the four ECU
  constants and one PC alias changed, with all other values and attributes
  preserved. Backup and corrected-file byte checks passed. No ECU write or new
  physical pressure check. Load the explicit corrected file, burn, fully remove
  ECU power including USB, then verify readback; oil pin changes require a power
  cycle per the firmware definition. Other reset findings remain unmodified.

## 2026-10-17 — Recover filters, TPS endpoints and crank-to-run fuel taper

User identified these reset differences for recovery and confirmed TPS27/185
came with the reset, not a new measurement. Restored from October10 reverted
baseline: TPS28/127; crankingEnrichTaper0.1→5.0s; filters TPS50,CLT180,IAT180,
O2 128,battery128,MAP20,baro64 (all previously zero). TPS physical closed/full
travel still needs checking; recovered values are historical calibration.
Preserved verified new injector/ignition wiring settings, oil/status inputs,
all maps, enrichment curves and PW Adder. Two independent map reviews pending.
This is recovery of selected baseline settings, not proof of a no-start cause.

Backup: `TurboExo_pre_filters_TPS_taper_recovery_2026-10-17_140406.msq`. Explicit load: `TurboExo_filters_TPS_taper_recovered_2026-10-17_140406.msq`; CurrentTune matches.
XML parsing, complete constants comparison (only10 expected changes), and
backup/output byte verification passed. Disk only: load/burn/readback pending;
no ECU write or new start test performed.

Map-review follow-up: independent fuel/AFR and ignition comparisons used matching
physical RPM/kPa coordinates. Atmospheric cranking region (250–600rpm,80–100kPa)
is nearly unchanged (VE delta0..+1.09 points; spark delta−1.375..0deg).
A specific low-speed VE difference exists at500rpm/66kPa:78.4→47 (−40%);
at600/66:64.6→48.5 (−25%). This is a possible catch-transition issue, not a
confirmed cause. Current VE/AFR/axes exactly match April3 legacy restore.
Both current load domains stop at100kPa; baseline extended to200kPa. Ignition
above100kPa uses the endpoint row, losing prior boost retard. No maps changed.
Firmware inspection also found current decelAmount0 versus prior100 causes
fuel cut during qualifying TPS deceleration events; left unchanged. PW Adder
uses a percentage of internal required fuel; prior Multiplier scaled calculated
fuel. User has not selected a change to those remaining settings.

## 2026-10-17 — Restore deceleration fuel amount to100%

User explicitly requested decelAmount100%. Previous saved value:0.0%.
Changed only decelAmount to100%, retaining normal fuel during qualifying TPS
deceleration events instead of a zero-percent fuel cut. No maps, wiring,
acceleration-enrichment method or other settings changed.
Backup: `TurboExo_pre_decel100_2026-10-17_140649.msq`. Explicit load file: `TurboExo_decel100_2026-10-17_140649.msq`;
CurrentTune.msq matches. XML, complete constants comparison and exact backup/output
byte verification passed. Disk only; load/burn/readback pending. No ECU write
or new start test performed; effect on the starting problem remains untested.

## 2026-10-17 — Scheduled 5° cranking timing test

User requested only CrankAng 10→5° and ignCranklock On→Off to test later
cranking spark after reported kickback. Preserved all other latest saved constants,
including newer changes relative to the 13:45 restore point.
Backup: `TurboExo_pre_crank_timing5_unlocked_2026-10-17_142233.msq`. Explicit load file: `TurboExo_crank_timing5_unlocked_2026-10-17_142233.msq`.
XML and full constant comparison passed; only those two constants changed.
Disk-only edit; ECU burn/readback and start result remain unverified.

## 2026-10-17 — Revert scheduled cranking timing test

User requested reverting the timing test after the 14:26 log showed no start.
Restored only CrankAng to 10° and ignCranklock to On from the pre-test backup.
All other current constants preserved. Backup: `TurboExo_pre_revert_crank_timing_2026-10-17_142902.msq`.
Explicit load file: `TurboExo_crank_timing_reverted_2026-10-17_142902.msq`. XML, full constant comparison and byte
verification passed. Disk only; ECU burn/readback pending. Supersedes the 5°
unlocked test.

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



## 2026-10-18 — Temporarily disable Pi automatic shutdown

- **Request:** Pi keeps turning off; disable automatic shutoff for now.
- **Change:** Removed `--poweroff` from repository and live UPS monitor unit, reloaded systemd and restarted monitor. Preserved key-state publishing and existing logging configuration. Backup: `/etc/systemd/system/pi-ups-monitor.service.before-disable-20261018`.
- **Validation:** Live service active and enabled; running command lacks `--poweroff`. Before modification it reported discharge at -0.423 A / 11.324 V.
- **Result:** Software shutdown disabled persistently until reenabled; hardware power loss remains possible. No tune changes.


## 2026-10-18 — Fuel restored; sequential fuel-scaling experiment prepared

- **Fuel supply:** User found cylinders 1 and 2 dry, measured sender at 110 ohms (consistent with bottom of travel/empty), added fuel, and reported the engine now tries to start. Subsequently reported wet plugs. Pump priming had not established fuel delivery. Fuel pressure remains unmeasured.
- **Baseline log:** `DataLogs/2026-10-18_13.46.14.mlg` (converted CSV alongside): peak 727 RPM, no settled idle, zero recorded sync losses; initial closed-throttle cranking PW approximately 49–54 ms at CLT 82°F, VE 100%, MAP 90–98 kPa, baro 99 kPa and logged Gammae 212%. User confirms deliberately holding full throttle during later attempts; zero-PW cranking rows all occur at TPS 100%. AFR echoes target throughout catches and is not a mixture measurement.
- **Scaling finding:** October18 11:33 restore point has reqFuel12.6/divider2; 12:07 has reqFuel25.2/divider4. User screenshot establishes the upper required-fuel entry remained12.6: TunerStudio calculated25.2 with one squirt and Alternating staging. Earlier explanation implying the user manually doubled the upper entry was incomplete. Firmware already compensates pulse size for sequential scheduling, so the saved25.2 doubles base fuel per cycle relative to12.6. Approximate logged calculation:25.2 ×1.00 VE ×0.94 MAP/baro ×2.12 correction +1ms opening ≈51ms. This uses the logged correction; it does not establish that current disk enrichment tables match the ECU during that log.
- **Test change/user confirmation:** User changed staging to Simultaneous, retained one squirt and upper required fuel12.6, cleaned all plugs, and restarted ECU. CurrentTune independently confirms reqFuel12.6, divider4, alternate Simultaneous, injLayout Sequential. No independent ECU readback. Current disk cranking IAC remains83% throughout; user confirms IAC is physically plugged in. No IAC increase is confirmed.
- **Hypothesis/expected result:** Correcting scaling should approximately halve the fuel portion of each pulse, giving roughly25–27ms under the same logged cranking conditions. Compare the next log for PW, catches and sustained idle. Cleaned plugs are an additional changed condition, so this is not an isolated fuel-only causal test.
- **Verdict:** Setup confirmed by user and disk; post-change start result pending. No tune edits made by assistant for this experiment.
- **Sources:** Speeduino202501.7 `init.cpp` sequential scaling https://github.com/speeduino/speeduino/blob/202501.7/speeduino/init.cpp#L572-L599 ; PW calculation https://github.com/speeduino/speeduino/blob/202501.7/speeduino/speeduino.ino#L1222-L1275 ; local `projectCfg/mainController.ini` alternate tooltip states staging is ignored for sequential firing but still affects reqFuel.


## 2026-10-18 — Sequential scaling test result (14:03:45 log)

- **Evidence:** Converted `DataLogs/2026-10-18_14.03.45.mlg` to CSV (1190 rows). Refreshed the13:46:14 CSV because its MLG had grown since initial analysis (now2967 rows). Both logs contain timestamp resets; do not use whole-file elapsed duration or analyzer's negative duration.
- **Result:** Closed-throttle, nonzero-PW cranking at100–399RPM: median PW20.546ms (18.347–25.913), versus49.460ms in the completed baseline. New logged Gammae mostly170% (baseline212%); CLT82–84°F. The reduction is larger than halving because total correction also fell. Approximate12.6ms ×0.91 MAP/baro ×1.70 +1ms ≈20.5ms, consistent with corrected effective scaling, not a full ECU readback.
- **Starting behavior:** Peak622RPM, no settled idle. Catches now occur with closed/slightly open throttle (33 of59 rows above400RPM atTPS<5), rather than predominantly full throttle. Catch MAP minimum79kPa versus88kPa baseline, but different throttle positions prevent attributing that difference solely to fuel correction. Zero recorded sync losses. IAC command remains83%. AFR equals target in all59 catch rows; no valid mixture diagnosis.
- **Verdict:** Intended pulse-width reduction observed; starting problem not resolved. Other changed factors include plug cleaning and logged total enrichment, so outcome does not isolate fuel scaling alone. No additional tune changes made.


## 2026-10-18 — Sustained running and closed-throttle idle confirmed (14:10:18)

- **User result:** Runs, but requires throttle to start; requested preserving this result.
- **Log evidence:** `DataLogs/2026-10-18_14.10.18.mlg` and converted CSV,1620 rows, no backwards timestamps. Continuous RPM>700 from252.893 to384.787s (131.894s), still running at log end. Battery13.0–14.4V during run, zero recorded sync losses. User's throttle-to-start report is consistent with logged starting throttle use.
- **Closed-throttle result:** Final30s TPS range0–0%, RPM995–1144 (median1071), MAP43–47kPa, PW4.446–5.060ms. CLT reaches151°F; this is not yet a fully hot idle validation.
- **IAC:** Logged cranking98–99%, not the previous83%. CurrentTune cranking table99% throughout; open-loop running table99/96/94/93/92/89/84/81/78/75%. End-of-log command82%. Thus this result also follows air-table changes and plug cleaning, not only fuel scaling correction.
- **Other observations:** Overall logged peak6835RPM and135kPa MAP; no boost/AFR calibration validation implied by this successful run. AFR was not validated in this analysis.
- **Milestone:** `TurboExo_running_sequential_fuel_scaling_fixed_2026-10-18_141358.msq`, byte-identical to CurrentTune at capture; `.sha256` covers snapshot, original log and CSV, `.provenance.txt` records limits. Saved reqFuel12.6, divider4, Simultaneous staging, injectionSequential, ignitionSequential, TrigAng0. Full ECU readback and physical ignition phase-swap confirmation remain absent.
- **Verdict:** Sustained running and closed-throttle idle established. Remaining issue: throttle needed to start. Preserve this snapshot before further changes.


## 2026-10-18 — AutoTune hot-running assessment (14:21:46)

- Latest log `DataLogs/2026-10-18_14.21.46.mlg` converted to CSV (4711 rows). First row has implausible CLT-40 and multiple zero channels; discard it. Remaining log spans5.812–455.702s (~450s) with engine already running throughout; no starting test here.
- Fully warm running: CLT194–207°F in valid samples; zero recorded sync losses, battery13.3–14.7V. Final30s TPS0%, RPM1380–1467 (median1440), MAP31–33kPa, PW2.730–2.949ms, CLT199–201°F, IAC77%. Holds hot idle, but speed remains high relative to historical850RPM target.
- AFR now varies independently of target: final30s13.3–14.0 (median13.8), target14.1–14.3 (median14.2). Consistent with slightly rich idle IF wideband calibration is correct. Sustained exhaust heat and no dominant echo improve interpretability; they do not independently validate analog calibration or controller status. No blanket approval of AutoTune mixture corrections.
- Disk diff: original running milestone and14:20:31 restorepoint have identical tune constants. CurrentTune changes103 VE cells:63 decreases/40 increases, -9 to+4 VE points. Some30–36kPa cells decreased, but all four cells surrounding the final hot idle (30/36kPa ×900/1500RPM) are unchanged. No other ECU constants changed; TS-only wueRecommended changed. This is consistent with user-reported AutoTune but does not establish burn/readback. Preserved `TurboExo_autotune_hot_run_2026-10-18_142146_DISK.msq` with SHA256 as post-AutoTune disk capture, not a validated full ECU readback or boost tune.
- Loaded engine excursions: logged peak6820RPM and136kPa MAP (~5.4psi above99kPa baro). Current fuel load axis still ends100kPa; AFR target at>100kPa is13.0. This run does not validate boost calibration; above100kPa the table uses its highest load row (MAP multiplication still applies). Additional boost-load bins/calibration needed before calling it boost-tuned.
- Verdict: Sustained fully warm closed-throttle idle confirmed; high idle and remaining wideband/boost calibration questions persist. No tuning changes made by assistant.


## 2026-10-18 — Successful hot-run tune preserved before boost preparation

User explicitly requested backup and successful-experiment record before updating tables/configuration. Saved `TurboExo_SUCCESS_hot_idle_autotune_pre_boost_extension_2026-10-18_202332.msq` byte-for-byte from CurrentTune, SHA256 `609ffa24ccccc9870e394b0bc5ce3758104459dc4ae66b71934c83d492c6a328`, with checksum and provenance sidecars. This preserves the current103-cell AutoTune VE revision following the successful14:21:46 hot-running log (final30s closed throttle1380–1467RPM,199–201°F). Successful sustained hot idle; high idle, starting behavior, AFR calibration and boost mapping remain separate open items. Disk snapshot, not independent ECU readback. No tune changes yet in this preparation step.


## 2026-10-18 — Boost table preparation after preserved successful hot run

- **Authorization:** User requested saving current successful tune, then updating tables/configuration, checking recorded valve identity, and researching a concrete bench-test rig. Intended operating boost target not yet supplied; no active boost target selected.
- **Backup:** `TurboExo_SUCCESS_hot_idle_autotune_pre_boost_extension_2026-10-18_202332.msq` plus SHA256/provenance. Associated successful14:21:46 run retained. CurrentTune matched backup before edits; guarded against concurrent TunerStudio changes.
- **Prepared tune:** `TurboExo_boost_table_preparation_PROVISIONAL_2026-10-18_202332.msq`; CurrentTune byte-identical at completion. Disk-only: load/burn/full ECU power cycle/readback remain required. No ECU write performed. All changes listed in `.changes.json`; checksum sidecar provided.
- **Tables:** Added120/140/160/180/200kPa to VE, AFR and ignition. Per-table retained NA bins preserve learned idle cells exactly. VE bins16/26/30/36/40/46/50/66/70/90/100; spark10/16/20/26/30/36/40/46/74/80/100; AFR16/26/30/36/40/46/50/60/70/86/100. Removing some old rows necessarily changes interpolation: maxima7.625VE points,1.286deg spark,0.08AFR at discarded original bin points. This is not a claim of all sub100 behavior unchanged. Existing duplicated RPM endpoint bins preserved for separate investigation.
- **Provisional boost seed:** AFR targets12.5/12.0/11.8/11.6/11.5 at120/140/160/180/200kPa copied from October10 historical preparation; not validated for current engine/fuel. Boost-only spark rows from same milestone, whose100kPa row exactly matches current; high-RPM values22/18/16/12/10deg. New VE uses current100kPa VE × current100kPa AFR target / new target, rounded nearest integer; assumes unchanged VE, encodes extra fuel directly because includeAFR/incorporateAFR remainNo. No extra MAP multiplier was added. These are starting assumptions, not demonstrated boost calibration. Lambda alias updated consistently with AFR.
- **Boost output:** ExplicitlyOff, OpenLoop with existingzero duty table; repaired RPM axis1500/2000/2500/3000/3500/4500/5500/6500 and TPS0/20/40/60/70/80/90/100; inactive base-duty lookup cleared from50% to0%. Pin/frequency/PID/min/max otherwise preserved and unvalidated; no pressure target enabled.
- **Protection correction:** engineProtectMaxRPM7000→1500. The existing120kPa absolute boost limit and SparkOnly cut remain. Firmware checkEngineProtect gates boost/oil/AFR protection above this RPM; previously7000 prevented cut below7000 despite excess MAP. This is a conditional protection RPM gate, not the ordinary rev limit. The relevant gate/boost-check code is identical in202501.6 and202501.7. Legacy Boost cut flag is cleared without being set in the inspected code, so earlier claim that its zero value proves no protection activation was too strong. Prepared tune should now cut above120kPa and the1500RPM gate (~3psi gauge near99kPa baro); do not interpret200kPa table coverage as a permitted boost target. Hardware/readback validation remains pending.
- **Hardware:** User images identify generic25mm atmospheric BOV advertised25psi and35A-AAA-DDBA-1BA3-port solenoid. Saved source screenshots and evidence limits in docs/REFERENCE.md and docs/WIRING.md. Earlier project notes had only 'bypass installed,' no exact model.
- **Validation:** XML parsing, expected13-constant diff, all retained rows exact,16×16 dimensions, strictly increasing load/boost axes, AFR/lambda byte equivalence, preserved fuel scaling/idle/modes/trigger, and CurrentTune/named-file byte equality checked. Independent review of12-constant table/output edit passed; gate correction separately reviewed. No functional ECU test yet.
- **Sources:** [Speeduino protection](https://github.com/speeduino/speeduino/blob/202501.7/speeduino/engineProtection.cpp), local mainController.ini menu labels, October10 historical milestone. Previous successful run does not validate these new settings.


## 2026-10-19 — Boost-table import units warning corrected (disk only)

The October 18 change from Closed Loop to Open Loop retained the old `boostTable`
units attribute. The local mainController.ini selects Duty Cycle % for Open Loop.
Corrected only `units="kPa"` to `units="Duty Cycle %"` in CurrentTune and
`TurboExo_boost_table_preparation_PROVISIONAL_2026-10-18_202332.msq`.
Preserved timestamped pre_units_fix copies and refreshed the prepared file checksum.
Verified XML parsing and byte equivalence apart from that label; all 64 cells remain
zero, boost output remains Off, and the two corrected files match exactly.
TunerStudio re-import and ECU readback remain unverified; no ECU write performed.
