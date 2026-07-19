# TurboExo — Status (living)

_Update whenever the loaded tune or the front line changes. Full history:
`EXPERIMENT_LOG.md`. Pinned facts: `docs/REFERENCE.md`._

## Loaded tune (2026-07-19)
`CurrentTune.msq` = **OEM stock injectors** + factory fuel baseline: reqFuel **12.7**
(correct for OEM inj), `injOpen` 1.0, `battVCorMode` "Whole PW", `crankingEnrichTaper`
5.0 s, `primePulse` ~30 ms, `CrankAng` 10°, `engineProtectMaxRPM` 4000, `crankRPM` 230,
`tpsflood` 60, factory-transplant VE. Snapshot: `restorePoints/TurboExo_2026-07-19_12.23.39.msq`.
> Test `2026-07-19_12.24.20`: revved to 893 rpm on a WOT blip only — no idle, never charged.

## Reference catch (what "running" looks like)
Only real catch so far: **07-09** (`TurboExo_VEfix_2026-07-09.msq`, reqFuel 7.0, on the old
RX-8 yellows) — climbed to 1212 rpm and the alternator charged to 14.1 V, **with ~11–14% throttle**.
The current OEM + factory-12.7 + factory VE is the config the engine ran on for years, so it
should be capable — the goal is to reproduce that climb.

## Next actions
1. **With-throttle catch on the OEM/factory baseline.** Crank with ~10–15% throttle (like 07-09),
   rev cap 4000 so let it climb; watch oil pressure. Grab the `.mlg` — this tells us if we're
   back to a real catch.
2. **Fuel is now off the table** (factory-known-good), so "won't climb/idle" is a **non-fuel**
   question — settle it with tests the logs can't (logs have no usable mixture: AFR echo):
   - **Give it air** (crack throttle / AAS base-air): climbs → air-limited; still stuck ~500 → not air.
   - **Plug read after a run** — the only mixture signal, *and* the #2 re-test.
   - **Does #2 fire** (cylinder-drop) — running on 4 vs 3.
3. **Idle air (for closed-throttle idle):** verify `iacPWMdir` + that the valve actually flows
   (sweep duty, watch RPM/MAP); AAS (not TAS) is the Miata base-air adjuster. Spray-test for a
   vacuum leak on the new turbo plumbing + injector seals.
4. **Ignition:** confirm idle-region timing is adequate (too little advance = weak/stalls).
5. **Battery discipline:** charged/jump, ≤5 s cranks — not the blocker, but removes a variable.

## Recently changed (2026-07-19)
- **Swapped RX-8 yellows → OEM stock injectors** (removes the yellow unknowns: dead-time, flow, #2 fouling).
- reqFuel 7.1 → **12.7** (factory value for OEM inj), `injOpen` 1.0, `battVCorMode` "Whole PW",
  `primePulse` ~30 ms, `fpPrime` 5 s, `primingDelay` 3 s, `engineProtectMaxRPM` → 4000.
- (07-12: `crankingEnrichTaper` → 5.0 s, `crankRPM` 230, `tpsflood` 60.)

## Known blockers
- **Idle air not proven** — IACV flow/direction (`iacPWMdir`), possible vacuum leak, base-air (AAS). Closed-throttle won't sustain.
- **Ignition at idle** — verify timing is adequate (untested at a real idle).
- **Cyl #2** — re-test now that all injectors are OEM: plug read after a run → clean = the yellow #2 injector was the fouler; still fouled = #2 spark/compression.
- **Battery** — low; charge to remove the variable (not the start blocker; ~10 V cranking is workable).
- **Wideband** unusable until ~15 s+ exhaust heat (AFR echo — read plugs, not logs).
- **Fuel** — now at the known-good factory baseline, so largely off the table.
