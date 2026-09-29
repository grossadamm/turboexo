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
