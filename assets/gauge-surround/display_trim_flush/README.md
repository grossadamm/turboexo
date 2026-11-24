# TurboExo flush display perimeter

This is a matched fascia and one-piece surround. The fascia keeps the approved soft glass-edge lip and replaces the scalloped outer frame with broad side borders and a tapered brow. The side lands are clipped to the original sidewall planes. A stepped receiver behind the curve blocks the view through the seam. The lower portions recede into the rail for removal clearance. The lower vehicle brackets remain exposed outside the screen surround. The matched front and driver views found no sightline through the seam in 77,968 sampled rays.

[Installed 3D viewer](assembly_view.html) · [Marked front edge before and after](before_after_annotated_front.png) · [Marked diagonal rail before and after](before_after_diagonal_rail.png) · [Driver view before and after](before_after_driver.png) · [Black ASA preview](assembly_black_ASA.png)

## Fit and hardware

All dimensions are millimeters. Display-local X points viewer-right, Y points up, and Z points toward the viewer, with the glass face at Z = 0.

- The fascia front is at Z = +2.30. At the main side lands the base face is at Z = +2.10. The two parts have a nominal 0.65 mm lateral seam allowance at the full-width sections. A shelf underlaps it by approximately 2 mm. The lower land recedes into the raised rails and the upper land follows the oblique roof underside.
- The approved aperture uses a 1.70 mm front web, a 151.48 × 95.18 mm throat, a 0.10 × 0.18 mm rear bevel and a 1.05 mm land. It has 0.35 mm nominal clearance to the glass face. The full 150.72 × 94.20 mm active rectangle clears the assembly on the screen normal and from recorded eyes 226, 236 and 244.
- All four OEM axes are retained at 173.70 × 98.40 mm. The fascia still bears on the four metal lugs. Use four fully threaded M3 × 0.5 × 14 mm button-head screws, four Ø6 × Ø3.2 × 0.50 mm flat washers, and the existing M3 hex nuts. The 5.90 mm fascia stack, 0.60 mm lug, 3.00 mm base web and 2.40 mm nut leave 1.60 mm of screw beyond the nut. The heads sit proud on the washers.
- Base edits are additive and limited to the two front side lands, the underside header and the rearward lower-left corner land. The roof, vehicle mount pads and slots, four lug seats and nut pockets retain their released geometry. The back remains open.

[Geometry and hardware audit](validation.json) · [Continuous base clearance](continuous_removal_check.json) · [Projection comparison](sightline_check.json) · [Screw and glass section](section_lug_and_glass.png)

## Bench assembly and removal

1. With the surround out of the car, load the retained nuts and support the LCD by its frame. Seat its lugs on the base. Clear print artifacts from the nut routes and bearing surfaces.
2. Offer the fascia up with the top tipped toward you about 10°. Guide the bottom into place by reversing the movement below. Check that all four pads sit flat against the metal lugs by hand before fitting washers and screws.
3. For removal, take out the four screws and washers and support the LCD. Tip the fascia top toward you about 10°, raise the bottom about 5 mm with a small shift toward viewer-right, then withdraw and continue lifting until the lower corners clear. Do this with the base out of the car. The path control points in the geometry audit give the exact tilt, lift and withdrawal sequence. The continuous CAD bound against the base is 0.121 mm. The smallest exact sampled clearance to the base is 0.165 mm. With the fascia removed, the display still lifts 10 mm and moves out 20 mm along the existing service route.
4. Verify the real glass clearance and free travel before tightening. The checks use nominal CAD. The ASA fit and finish are pending a physical bench trial.

## Files

| Part | CAD and mesh | Print project |
| --- | --- | --- |
| Fascia | [STEP](display_trim.step) · [Face-down STL](display_trim_face_down.stl) | [P1S ASA 3MF](display_trim_P1S_ASA.3mf) |
| Matched one-piece surround | [STEP](surround.step) · [STL](surround.stl) | [P1S ASA 3MF](surround_P1S_ASA.3mf) |
| Installed reference assembly | [STEP](display_trim_assembly.step) · [3MF](display_trim_assembly.3mf) | |

Both projects were sliced offline in Bambu Studio for the P1S, 0.4 mm nozzle, Generic ASA, 0.20 mm layers and four walls. The fascia is face-down with a 6 mm brim. The base uses the approved 55° orientation, snug support and an 8 mm brim. The slice estimates are **36 min 35 s and 11.78 g** for the fascia and **9 h 16 min and 264.39 g** for the base. No print or upload was started.

[Fascia slice audit](slice_validation.json) · [Base slice audit](print_validation.json) · [Release checkpoint](checkpoint.json)

## Editable source

The [editable source archive](editable_source.zip) and [CadQuery geometry](src/build_trim.py) use the original surround STEP and its model-to-display transform from the sibling `upper_mount_revision`. The loaded baseline STEP is the editable revision's foundation. It keeps the original structural geometry and fuses the modeled lands onto it.

Keep this directory beside `upper_mount_revision`, `display_trim_soft_lip` and the existing print review folders. With the provided Python at `/Users/adamgross/dev/artifacts/gauge-surround-2026-11-13/.venv/bin/python`, run:

```text
src/build_trim.py
src/validate_trim.py
src/check_removal.py
src/check_sightlines.py
src/render_trim.py
src/slice_trim.py
src/slice_base.py
src/slice_base.py verify
```
