# Pre-scan checkpoint · front wing and brake ducts

[Open the combined rotatable viewer](deliverables/sweep30_duct_study/rotate.html). It opens offline with the driver-side progressive scoop visible. **Duct outlet** shows the turning vanes. **Passenger mirror** toggles an interference study on the opposite side. The combined GLB includes that extra mesh; generic GLB viewers may display it immediately.

## Design state

- The approved chin, compressed corner gasket, 36° channel floor and 42° upper blade are saved in the [closed-joint checkpoint](../closed42-2026-11-24/README.md) at commit `b36ab0f`, independently reviewed in `de4cb0b`.
- The [30° passenger-side crest](deliverables/sweep30_study/wing_right.step) is a styling and flow study. Its exit is 10.07 mm farther outboard than the approved 16° crest. The driver side of the combined assembly still shows the 16° wing. [Overhead comparison](deliverables/sweep30_study/views/compare_top_16_vs_30_detail.png)
- The [progressive driver-side scoop](duct_progressive_turn/TurboExo_brake_scoop_progressive_turn_mm.stl) is the duct-thread baseline. The vanes increase to 30°, 36° and 42° of outward turn. The duct and wing remain distinct parts. The passenger scoop in the viewer is a bracket-registered mirror.
- CAD uses millimetres in the car frame, with +X forward, +Y car-left and +Z upward. Standing in front of this left-hand-drive car, the driver side is on your right. GLB coordinates are metres, ordered (car Y, car Z, car X).

## Keep for the scan session

Register the scan to the existing metal plate faces and retained hole axes. Capture both bumper undersides, the webs and diagonal braces, the available space behind each outer plate, and the wheel/inner sidewall. Record the steering and suspension position with each scan. The existing wheel bodies are illustrative envelopes.

The modeled driver-side duct clears the wing, chin, fiberglass and seal, but overlaps the outer plate and aft receiver. On the passenger side the trial mirror clears the 30° wing by about 11 mm in the sampled static placement, but crosses the chin, fiberglass, seal and mounting hardware. Fit each side from its own scan before printing the ducts. Revisit the obsolete rectangular mounting rail when detailing the carbon spars and any aluminum retention brackets. [Registration and interference results](deliverables/sweep30_duct_study/right_registration.json)

## Flow and print history

[Blade-on/off CFD](deliverables/cfd_corner_study/REPORT.md) and [16° versus 30° CFD](deliverables/sweep30_study/REPORT.md) include numerical results, geometry, solver code and comparison figures. The extra sweep steered air farther outward within the channel. The simplified model showed little average flow-direction change just ahead of the tire. The comparison predated adding the ducts. No combined wing-and-duct performance or physical clearance has been validated.

The [two-plate P1S Generic PLA project](deliverables/closed42_joint/right_fit/closed42_right_fit_draft_pla_p1s.3mf) is the earlier **passenger-side, 16° crest** fit trial. Plate 1 is the inner chin with rectangular mounting rail; plate 2 is the complete outer wing. Neither plate contains a brake duct. Only plate 1 was confirmed started in white PLA. Completion and on-car fit were not verified here.

## Restore

The combined viewer is self-contained. Run `shasum -a 256 -c SHA256SUMS` from this directory to verify the saved files. For viscous-flow analysis using the individual time snapshots, run the following in `deliverables/cfd_corner_study/section`:

```sh
for archive in snapshots/*.tar.gz; do tar -xzf "$archive"; done
```

The per-snapshot digests are in [the archive manifest](deliverables/cfd_corner_study/section/snapshots/members.json). See [RESTORE.md](RESTORE.md) for dependencies and regeneration scope.
