# TurboExo — Status (living)

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

## Loaded tune (2026-07-19, verified live 2026-07-25)
`CurrentTune.msq` = **OEM stock injectors** + factory fuel baseline: reqFuel **12.7**,
`injOpen` **1.0**, `battVCorMode` **Whole PW**, `crankingEnrichTaper` **5.0 s**,
`primePulse` 30/30/25/25 ms, `CrankAng` 10°, `engineProtectMaxRPM` **4000**, `crankRPM` 230,
`tpsflood` **60**, factory-transplant VE.
Back-solving PW from `2026-07-25_09.33.18` gives reqFuel 12.73 — **the file matches what's
burned.** Snapshot: `restorePoints/TurboExo_2026-07-19_12.23.39.msq`.

## Next actions
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

## Known good — stop re-testing these
Trigger / full sync (status 2, 0 sync loss all morning). Base timing (timing light, within 1°).
MAP plumbing and sensor (moves 39–100 kPa). Fuel config (factory 12.7 baseline, verified live).
`IgInv` "Going Low". The IACV itself.
