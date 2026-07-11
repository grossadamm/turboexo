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
1. **Charge the battery / jump pack.** Recent cranks sag to 9.6–10.3 V; nothing is
   valid below alternator-charging voltage. ≤5 s cranks, dry plugs.
2. **Clean closed-throttle test of the lean-out** (7.1 + reverted VE). Watch for a
   catch that pulls MAP toward idle vacuum instead of flooding at ~95 kPa.
3. **Re-read plugs.** If #1/#3/#4 clean up and only **#2** still fouls → swap
   injector **#2 ↔ #1** and see if the heavy soot follows the injector.
4. ~~Raise `engineProtectMaxRPM` off 1500~~ — **done (now 3000)**; won't fuel+spark-cut at fast-idle.
5. If it catches then immediately dies (starved, not flooded): bump
   `crankingEnrichTaper` toward ~1.0 s.

## Recently changed (2026-07-11)
- reqFuel 7.9 → 7.1 (corrected injector anchor: 238 cc, not 265).
- Reverted 6 idle-region `veTable` cells to `VEfix` (undid the 07-10 idle-vacuum
  trap — ~80% of the over-fuel; reqFuel was the other ~20%).
- `engineProtectMaxRPM` 1500 → 3000 (was a fuel+spark cut at the idle target).

## Known blockers
- Battery weak (no true run since 07-09).
- IACV airflow not proven (idle-air; MAP unchanged closed-throttle when powered).
- Cylinder #2 hardware (sooty on a fresh plug; injector / coil tower / compression).
- Wideband unusable until ~15 s+ exhaust heat (AFR echo — don't tune fuel from logs).
