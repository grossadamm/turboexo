# TurboExo — First-Start Commissioning Checklist

**Situation:** Complete rewire + NA→turbo conversion + UA4C Speeduino swap. Engine has
**never run** in this configuration. Nothing is trusted yet — not sensors, not the trigger,
not fuel pressure, not the turbo oil supply.

**Tune to load:** `TurboExo_FirstStart.msq` (regenerate any time with the pipeline in
`BOOST_TUNE_NOTES.md` §9). It carries every commissioning and safety setting: pump prime +
delayed priming pulse + afterstart and warmup enrichment (all were zero — the engine
literally could not start, and would have stalled even if it caught), accel enrichment
restored (zeros also cut all fuel on every throttle close), Cycle-Average MAP sampling,
ADC filtering, "new ignition mode" on, AFR lean protection armed for the boost window,
protection cuts set to fuel+spark, boost solenoid disabled (wastegate spring only), and
knock mode OFF (the raw knock sensor is unreadable without a conditioner — Phase 7).
**All setting values live in the notes (§7) — this checklist is the procedure.**

> ⚠️ **The base tune itself is unproven.** The Speeduino has never started this car.
> Treat the *entire* VE table, cranking enrichment, and warmup curves as starting
> estimates. Expect the wideband to disagree with the AFR target everywhere at first;
> that's normal and it's what Phase 6 fixes. The boost rows were extrapolated from this
> **unverified** anchor — see Phase 7.

Work through the phases **in order**. Each phase proves the things the next phase depends on.

---

## Phase 0 — Bench checks (key OFF or key ON, engine never cranked)

- [ ] **TunerStudio connects** to the UA4C and firmware reports `2025.01.7` (matches what the tune was built against).
- [ ] **Burn the tune** and read it back — confirm no "controller settings differ" warnings.
- [ ] **Sensor sanity, key on / engine off** (engine cold, sat overnight):
  - CLT ≈ IAT ≈ actual ambient temp, within a few °F of each other. If either is pegged at −40 or +300, the wiring or calibration is wrong.
  - MAP ≈ Baro ≈ ~100 kPa (or local pressure). The Baro-mode fueling *depends* on a sane baro reading — verify it specifically.
  - Battery voltage gauge reads ~12.4–12.8 V engine off (matches a multimeter on the battery).
- [ ] **TPS calibration:** Tools → Calibrate TPS. Closed = 0%, floored = 100%, sweep is smooth with no dropouts (dropouts = wiring/connector problem).
- [ ] **Wideband (14Point7 Spartan 3 OEM, LSU 4.9):** no free-air calibration needed or supported — the LSU 4.9's connector carries its factory calibration. Verify instead: sensor in open air, key on, ~30–60 s heater warm-up → TunerStudio AFR gauge pegs at **~20.0** (ECU cal is linear 0–5 V = 10–20 AFR, burned 2026-06-06). Exhale on the tip: momentary rich dip. If it pegs at 10.0 or wanders, check the analog wire and the Spartan-to-ECU sensor ground (ground offset = AFR error; 0.1 V ≈ 0.2 AFR). The whole tuning plan rests on this signal.
- [ ] **Fuel pump prime:** key on — pump should run a few seconds and stop. Listen for it; check the pump relay wiring survived the rewire.
- [ ] **Throttle/return spring, all fluid levels, battery charged or on a maintainer** (lots of cranking ahead).

## Phase 1 — Trigger verification (cranking, NO fuel, NO spark)

Pull the fuel pump fuse (or unplug injectors) **and** unplug the coils.

- [ ] Crank and confirm **stable RPM** in TunerStudio (~150–300 rpm, not jumping around or dropping to 0).
- [ ] Run the **composite logger** (Diagnostics → Tooth/Composite Logger) while cranking: clean Miata 99-05 pattern, no sync losses. Check the `Sync loss counter` stays at 0.
- [ ] If RPM is erratic: check CKP/CMP wiring, shielding/ground (a full rewire makes this the #1 suspect), and try TrigFilter at a stronger setting only as a last resort. Do **not** change the trigger edges — they are correct per the wiki (notes §7.4).

## Phase 2 — Fuel system (still no start)

This is a **new fuel system under future boost** — leak-check it like it matters, because it does.

- [ ] With injectors still disabled, reinstall the pump fuse, key on, and verify **fuel pressure ≈ 43.5 psi (3 bar)** on a gauge. All the injector math assumes exactly this (notes §4).
- [ ] Pressurize and **inspect every fitting** — pump, filter, rail, FPR, return — for weeping. Wipe, wait, re-check.
- [ ] Optional but worthwhile: pull a plug, crank briefly with injectors connected, confirm plugs are wetting (injectors actually firing and wired to the right driver banks).

## Phase 3 — Spark & base timing

- [ ] Coils reconnected, fuel disabled again. Crank and verify **spark on all cylinders** (spark tester or grounded plug). Wasted spark pairs: 1–4 and 2–3 — confirm the coil wiring matches.
- [ ] **Base timing check:** in TunerStudio set *Fixed timing* (Spark Settings → fixed advance) to 10°. Stock NB sensors usually land close, but **verify with a timing light**, don't assume.
  - You can do this while cranking, or (better) right after first start at idle.
  - A few degrees off → trim `TrigAng` until the light shows 10° at the crank pulley mark. Way off → suspect CKP/CMP wiring or swapped coil pairing (1–4 vs 2–3); do **not** flip trigger edges (notes §7.4 / §8).
  - The tune turns on "Use new ignition mode" (required for this decoder) — it takes effect on burn, no ECU power-cycle needed, but the timing-light check is the proof.
  - **This must be right before any load tuning** — every number in the spark table is meaningless otherwise.
  - Set fixed timing back to *Off* when done.

## Phase 4 — Turbo oil priming (do NOT skip)

A dry turbo at first start is how center sections die in the first 30 seconds.

- [ ] Verify oil **feed and drain** line routing — drain must run downhill, above the oil level, no kinks.
- [ ] With fuel and spark disabled, **crank in ~10s bursts until oil pressure shows** on the gauge (rest the starter between bursts). This fills the turbo feed line.
- [ ] Even better: pre-fill the turbo feed line / pour clean oil into the feed fitting before connecting.

## Phase 5 — First start

- [ ] Have a fire extinguisher within reach. New fuel lines + first start is the highest-risk moment.
- [ ] Re-enable fuel and spark. **Key-cycle 2–3 times** (key on, let the pump prime, key off) before the first crank — the rail and lines have never been wet, and the priming squirt is timed to fire after pump prime, so full pressure first.
- [ ] Start **datalogging before cranking** — if it doesn't start, the log tells you why. Rule of thumb: cranks 5+ s without firing → log RPM + pulsewidth; PW = 0 is a corrections problem, PW > 0 with no fire is spark/trigger.
- [ ] Crank. It may need a small throttle blip to catch. Expect ugly — it just needs to *run*.
- [ ] **First 30 seconds:** watch oil pressure (must come up immediately — if not, shut down), and look/smell for fuel, oil, or coolant leaks. Shut down for any of them.
- [ ] If it starts and dies repeatedly: cranking/ASE enrichment is the usual suspect — log it and adjust, don't just keep cranking. The priming pulse, ASE, and warmup curves are research-based starting estimates, not tuned values (notes §7.2–7.3).
- [ ] Let it warm up to operating temp. Watch CLT climb sanely, fans trigger, no leaks at the turbo oil lines (they're new), coolant burped.
- [ ] **Re-verify base timing at idle** with the timing light (fixed 10° again) — more accurate than during cranking.

## Phase 6 — Tune the entire NA region (wastegate spring only, stay out of boost)

The base VE table has never run this engine, so this is a full from-scratch NA tune,
not a touch-up:

- [ ] Get a stable warm idle: idle valve settings, then VE at the idle cells against the wideband. (Keep EGO closed-loop OFF throughout tuning.)
- [ ] Tune warmup enrichment over a few cold starts (one per morning is the honest way).
- [ ] Road-tune VE across the **whole vacuum region** (steady-state cells first, then transients/accel enrichment), driving gently — no WOT yet.
- [ ] Then tune the **100 kPa row at WOT** in a low gear, short pulls, watching the wideband. This row is the anchor everything above it hangs off.
- [ ] Verify **no boost is possible yet**: boost control off / lowest wastegate spring pressure, and confirm the **boost cut is armed** as the backstop (value: notes §2).

## Phase 7 — Then, and only then: the boost plan

Because Phase 6 will have changed the VE table, the extrapolated boost rows are stale:

1. **Regenerate the boost rows from the freshly tuned NA tune:** run the notes §9 pipeline (generator, then **always** the patch script) with the generator's `FIRST_START_SHAPING` flag set `False` — the road tune has replaced those first-start floors.
2. **Knock hardware:** the sensor is wired raw to the analog input — Speeduino can't read it, so knock mode is OFF. Install a conditioner module (part options and band-pass spec: notes §7.1), feed its 0–5 V output to the knock pin, set knock mode to Analog, calibrate the threshold at clean WOT, then set the generator's `KNOCK_BLIND` flag `False` and regenerate (restores the extra spark it was holding back). Until then, knock protection = conservative timing + rich AFR + your ears.
3. **Oil-pressure protection gate — do this BEFORE ramping boost:** fit an analog oil-pressure sender on a spare UA4C analog input (verify no pin collision with the raw knock-sensor wire), enable the oil-pressure input + protection, and populate the protection minimums (suggested values: notes §10).
4. **Confirm the boost solenoid hardware first** (part number + 3-port plumbing; solenoid-dead must equal spring-only — notes §7.3b), then run **spring-only pulls** with the solenoid at 0%/unplugged and confirm ~148–150 kPa before closing the loop. Then re-enable boost control (`boostEnabled` → On). The closed-loop constants were already cleaned (uninitialized gain, slow PID interval, reversed TPS axis, 30 Hz valve frequency — notes §7.3b; `boostFreq` needs an **ECU power-cycle** to take effect); keep `boostDCWhenDisabled` at 0% so below the enable threshold the valve stays unpowered (pure spring).
5. **Ramp boost incrementally toward the target** (target and cut values: notes §2 and header), watching AFR at every step. The armed AFR lean protection (window values: notes §7.2) is a backstop, not a substitute for watching the wideband. **Never enable closed-loop EGO in boost.**

---

### Quick reference — what `TurboExo_FirstStart.msq` has set

All values live in `BOOST_TUNE_NOTES.md` (single source of truth — §2 key facts, §7
settings, §7.4 verified-correct list). In brief: trigger and ignition match the Speeduino
wiki for this car (never flip trigger edges); pump prime, delayed priming pulse, ASE,
warmup, and accel enrichment are all populated starting estimates (they were zeros);
MAP sampling is cycle-averaged; AFR lean protection is armed for the boost window;
protection cuts are fuel+spark; boost solenoid and knock mode are OFF until Phase 7;
EGO is open-loop; the AFR table is display-only (richening lives in VE).
