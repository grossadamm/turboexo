# ASA intake printing on the Bambu P1S

Recorded 2026-11-02 from the November 1–2 calibration and intake-preparation
session. These are this spool's working settings, not universal ASA constants.
Printer: **Bambu Lab P1S, standard-flow 0.4 mm nozzle**; slicer verified during
the session: **Bambu Studio 2.8.2.61**. Filament brand/product/color were not
established. The intended parts are the TurboExo intake and filter holder.

## Current working settings

The filament preset is **ASA - P1S 265C 8.8mm3s**, derived from Generic ASA.
The final saved intake project and preset were read back on 2026-11-02.

| Setting | Value | Basis |
|---|---|---|
| Nozzle, initial and subsequent layers | **265°C** | User selected after temperature tower |
| Maximum volumetric speed | **8.8 mm³/s** | 20% below inferred onset at approximately 11 mm³/s |
| Flow ratio | **0.9975** | Coarse +5 patch: 0.95 × 1.05 |
| Flow Dynamics / pressure advance K | **0.040** | User selected PA Pattern result |
| Plate | **Textured PEI** | Selected project plate |
| Bed, initial and subsequent layers | **100°C** | Saved ASA settings |
| Part fan, first 3 layers | **0%** | Saved preset |
| Normal part cooling | **10–35%** | Final authorized change; maximum reduced from 80% |
| Minimum-fan layer-time threshold | **35 seconds** | Inherited ASA setting |
| Maximum-fan / slowdown layer-time threshold | **3 seconds** | Inherited ASA setting |
| Overhang/bridge fan | **80%** | Retained separately from normal cooling |
| Auxiliary fan | **0%** | Saved preset |
| Layer height | **0.20 mm** | Intake project |
| Wall loops | **4** | User-authorized change from 2 |
| Infill | **5% gyroid** | Retained intake project setting |
| Brim | **10 mm, outer only** | User requested adhesion improvement |
| Brim-object gap | **0.1 mm** | Retained removal gap |
| Outer wall speed | **60 mm/s** | Retained project setting |
| Inner wall requested speed | **300 mm/s** | Actual speed constrained by volumetric flow and other limits |
| Supports | **Automatic tree, build plate only** | Retained orientation/support setup |
| Support top Z / object XY separation | **0.2 / 0.35 mm** | Retained project settings |

Normal cooling is interpolated by layer time, not a constant 35% fan command.
The separate 80% overhang setting can still apply. First-layer behavior and
overhang behavior should be judged from the sliced job, not only this table.

## Calibration evidence and interpretation

1. **Temperature tower:** requested sweep 270→250°C in 5°C steps. User reported
   that sections looked roughly the same and chose **265°C**. No measured
   mechanical-strength comparison was recorded.
2. **Maximum flow:** requested start **5**, end **20 mm³/s**, step **0.5**.
   User reported defects at the **sixth visible side marking**. Inspection of
   Bambu's actual `SpeedTestStructure.step` geometry showed markings every
   **2 mm**, starting at approximately 2 mm. Sixth mark ≈12 mm;
   `5 + 12 × 0.5 ≈ 11 mm³/s`, then `11 × 0.8 = 8.8 mm³/s`.
   This supersedes the earlier rough 10 mm³/s suggestion based on “halfway.”
   The print's exact temperature was not independently verified: when the
   still-open max-flow project was inspected later, it showed 260°C before
   the final 265°C preset was saved. Treat 8.8 as the adopted working limit,
   not a rigorously measured limit at 265°C.
3. **Pressure advance:** Bambu's PA Pattern generator, **K 0–0.05 in 0.005
   steps**. Exported G-code was checked for the K sweep and 265°C print target.
   User selected **0.040**. A printer record named **ASA 265C K0.040** was
   saved for Generic ASA / 0.4 mm and assigned to **AMS A4**. Reopening A4's
   material settings confirmed **0.040**. Choose the pattern with even line
   width through corners: low K bulges; high K pinches or gaps.
4. **Coarse flow ratio:** baseline **0.95**, nine patches −20 through +20 in
   5% increments. User selected **+5**. Saved ratio **0.9975** was verified
   on disk. Judge the central top surface for joined lines without open gaps
   or raised ridges; ignore labels and isolated edge blemishes.
5. **Fine flow ratio:** a ten-patch 0 through −9 test was prepared using
   **0.9975** as its baseline. The user explicitly **skipped it**. No fine
   result exists. For these percentage patches, a later adjustment would be
   `new ratio = current ratio × (100 + patch modifier) / 100`.

The reduction to 35% maximum normal cooling was authorized after calibration;
it has no reported full-part validation yet. No VFA speed test was completed.

## Saved artifacts and restoring the setup

Repository archive: [printing/asa_2026-11-02/](printing/asa_2026-11-02/).

- [Final intake project](printing/asa_2026-11-02/intake_4walls_cooling35.3mf):
  four walls, updated cooling, calibrated extrusion, existing two-plate layout.
- [Filament preset](printing/asa_2026-11-02/ASA_P1S_calibrated.json): user overrides
  inheriting Generic ASA. Future Bambu defaults may differ; use the project
  and verified settings record to check effective values.
- [Verified settings and K assignment](printing/asa_2026-11-02/verified_settings.json).
- [Coarse calibration project](printing/asa_2026-11-02/flow_rate_coarse_baseline095.3mf):
  preserves the original 0.95 baseline and per-object modifiers.
- [PA calibration G-code](printing/asa_2026-11-02/pressure_advance_K0_to005.gcode):
  historical calibration job, **not the intake print file**.
- [Source locations](printing/asa_2026-11-02/provenance.json) and
  [SHA-256 checksums](printing/asa_2026-11-02/SHA256SUMS).

Last opened working project:
`/Users/adamgross/Downloads/Air Intake - 4 walls - ASA cooling35.3mf`.
The live user preset was saved under BambuStudio's user filament directory;
its original absolute location is recorded in provenance.json.

Open the final intake project in Bambu Studio, verify the values above, and
**slice again before printing**. The final four-wall / 35% cooling reslice
was not completed because computer control failed. Earlier approximately
15-hour / 245–251 g estimates belonged to older slices; do not treat them as
the final job estimate. Preserve any newer manual project changes.

**K is separate from the portable filament preset.** Check Device → A4 →
Materials Setting → PA Profile for **ASA 265C K0.040**, Factor K **0.040**.
If restoring to another printer or after records are lost, use Calibration
tab → Flow Dynamics → Manage Result → New to recreate it, then assign A4.
Changing a slicer file does not itself establish the printer's K assignment.

## Bambu Studio navigation

The in-window **Calibration tab** provides guided manual Flow Dynamics and
Flow Rate workflows for the P1S. The separate **macOS Calibration menu**
provides Temperature, Pressure advance, Flow rate → Coarse/Fine, and
More… → Max flowrate/VFA. In the verified version, **Preferences → Other →
Develop mode** exposes those extra menu generators for Bambu printers.
They generate the parameter changes; a bare tower STL does not.

Use Standard / 100% printer speed for calibration. Keep maximum volumetric
speed, flow ratio, and K distinct: they respectively limit extrusion speed,
scale deposited volume, and compensate pressure during speed changes.

## Preheat and remaining checks

- User requested bed preheat to **100°C**; the Device target was set and
  rising temperature verified on November 2. This is a historical action,
  not evidence that the bed is currently powered or ready.
- At the live fan check, part, auxiliary and chamber fans were all off.
  The saved 70% exhaust parameter is gated off in this P1S profile:
  `support_air_filtration=0`; startup explicitly sends `M106 P3 S0`.
  Do not mistake the inactive parameter for a commanded 70% exhaust speed.
- Approximately 30 minutes of closed-door 100°C bed preheating was suggested,
  not measured or established as a Bambu P1S requirement. Chamber temperature
  was not measured.
- Full intake print completion, fit, support removal, airtightness, mounting
  durability and engine-bay thermal performance have **not been reported**.
  Inspect support access inside the curved passage. The brim improves base
  attachment; it does not establish resistance to splitting higher up.
- Exact ASA manufacturer/product remains unknown. Bambu's 92–100°C
  load-dependent heat-deflection figures use annealed specimens and are not
  continuous-service ratings for this unvalidated engine-bay part.

## Sources checked during the session

- [Bambu Studio 2.8.2.61 flow-test model](https://github.com/bambulab/BambuStudio/blob/v02.08.02.61/resources/calib/volumetric_speed/SpeedTestStructure.step)
  and [height-based G-code ramp](https://github.com/bambulab/BambuStudio/blob/v02.08.02.61/src/libslic3r/GCode.cpp#L4724).
- [Calibration menu and Develop-mode logic](https://github.com/bambulab/BambuStudio/blob/v02.08.02.61/src/slic3r/GUI/MainFrame.cpp).
- [Orca upstream volumetric-flow interpretation](https://github.com/OrcaSlicer/OrcaSlicer/wiki/volumetric_speed_calib)
  and [flow-ratio calibration](https://github.com/OrcaSlicer/OrcaSlicer/wiki/flow_ratio_calib).
- [Bambu ordinary ASA technical data sheet](https://store.bblcdn.eu/s8/default/cad72d633f104a1aa80dc6c5937cb642/Bambu_ASA_Technical_Data_Sheet.pdf):
  45–60°C chamber guidance, 80–100°C bed, 240–270°C nozzle and thermal-test conditions;
  applies to Bambu ASA, not automatically every ASA formulation.
- [Polymaker layer adhesion](https://wiki.polymaker.com/printing-tips/common-printing-issues/poor-layer-adhesion)
  and [Prusa perimeter guidance](https://help.prusa3d.com/article/layers-and-perimeters_1748).
