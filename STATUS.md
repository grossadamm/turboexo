# TurboExo — Status (living)

_Update whenever the loaded tune or the front line changes. Full history:
`EXPERIMENT_LOG.md`. Pinned facts: `docs/REFERENCE.md`._

## Loaded tune
`CurrentTune.msq` = **`TurboExo_revcap3000_2026-07-11.msq`**: reqFuel **7.1**,
idle-region `veTable` cells reverted to `VEfix` (500 rpm 40/46/50/60 kPa =
41/45/47/46; 700 rpm 50/60 kPa = 50/49), `battVCorMode` "Open Time only",
`crankingEnrichTaper` 0.1 s, `CrankAng` 10°, `engineProtectMaxRPM` 3000 (raised from 1500).
> Not yet burned/tested at time of writing — confirm reqFuel 7.1 + `engineProtectMaxRPM` 3000 in TunerStudio and burn.

## Last-known-good
`TurboExo_VEfix_2026-07-09.msq` (reqFuel 7.0) — only tune that self-sustained
(1212 RPM, ~2.5 s, alternator charged to 14.1 V).

## Next actions
1. **Keep cranks ≤5 s (charge/jump helps, but voltage is NOT the blocker).**
   Cranking sits ~10 V, which is workable; only *long* cranks sag to 6.5–7.6 V,
   where spark weakens and injector dead-time balloons (fuel leans). The good run
   cranked at ~10.9 V too — its 13–14 V came only after it caught (alternator).
   The last run had ~10 V and still didn't sustain, so the catch is limited by
   mixture/air, not charge.
2. **Clean closed-throttle test of the lean-out** (7.1 + reverted VE). Watch for a
   catch that pulls MAP toward idle vacuum instead of flooding at ~95 kPa.
3. **Isolate cyl #2 — plug RULED OUT** (a swapped/clean plug re-fouled #2; 1/3/4
   only light). Prime suspect = **injector #2**: the used RX-8 yellows are the main
   new variable, and because injection is paired (2+3 share the driver/wiring), only
   the *physical* injector can single out #2 vs the clean #3. Test — ohm #2 vs the
   others, then **swap injector #2 ↔ #1**: soot follows injector = leak/over-flow
   (clean/flow-test/replace); stays at #2 = #2's individual spark wire/boot (the
   rewire touched it). **Compression is a low-probability last resort** — the engine
   ran before, internals untouched, and mild variance wouldn't stop it firing.
   A dead/weak #2 alone would make idle hard (running on ~3).
4. ~~Raise `engineProtectMaxRPM` off 1500~~ — **done (now 3000)**; won't fuel+spark-cut at fast-idle.
5. If it catches then immediately dies (starved, not flooded): bump
   `crankingEnrichTaper` toward ~1.0 s.

## Recently changed (2026-07-11)
- reqFuel 7.9 → 7.1 (corrected injector anchor: 238 cc, not 265).
- Reverted 6 idle-region `veTable` cells to `VEfix` (undid the 07-10 idle-vacuum
  trap — ~80% of the over-fuel; reqFuel was the other ~20%).
- `engineProtectMaxRPM` 1500 → 3000 (was a fuel+spark cut at the idle target).

## Known blockers
- Battery low (rests ~11.5 V, sags on long cranks) — degrades long cranks, but not the start blocker (last run cranked ~10 V and still didn't sustain).
- IACV airflow not proven (idle-air; MAP unchanged closed-throttle when powered).
- Cyl #2 hardware — **confirmed positional** (a swapped plug re-fouled #2 while 1/3/4 stayed light); injector over-flow, weak spark path, or low compression. May be why it won't hold idle (effectively running on ~3).
- Wideband unusable until ~15 s+ exhaust heat (AFR echo — don't tune fuel from logs).
