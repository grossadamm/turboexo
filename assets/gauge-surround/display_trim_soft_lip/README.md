# TurboExo soft-lip display fascia

The one-piece fascia has a shallow inner lip that lowers the edge toward the inactive glass border. A small rear bevel leads into a 1.05 mm flat land, which tapers back into the original web. The revision uses the approved surround from `upper_mount_revision` and the existing four lug seats. The final part is intended to be black ASA. Blue identifies the fascia in the CAD views.

[Interactive installed assembly](assembly_view.html) · [Before and after section](section_before_after.png) · [Lug and screw section](section_lug_and_glass.png) · [Driver view](assembly_oblique.png)


## Files

- [Face-down STL](display_trim_face_down.stl) and [P1S ASA project](display_trim_P1S_ASA.3mf) for printing the fascia.
- [Fascia STEP](display_trim.step) and [fascia STL](display_trim.stl) in the approved surround's assembly coordinates.
- [Assembly STEP](display_trim_assembly.step) and [assembly 3MF](display_trim_assembly.3mf) contain the installed surround, fascia, OEM frame and both glass layers, and four hardware stacks. These are inspection files in assembly coordinates. Print using the face-down STL or ASA project above. PCB and flex checks use the vendor component envelopes.
- [CadQuery source](src/build_trim.py), [geometry validation](validation.json), [continuous base-clearance check](continuous_removal_check.json) and [slice and toolpath audit](slice_validation.json).

## Dimensions and fit

In display coordinates, X is viewer-right, Y is up, and Z is toward the viewer. Z = 0 is the OEM glass face. All dimensions are mm.

| Feature | Nominal dimension |
| --- | --- |
| Fascia envelope | 182.74 × 112.10 × 5.90 |
| Fascia width at mid-height | 167.92 |
| Front web | 1.70 thick, face at Z = +2.30 |
| OEM body | 164.80 × 109.30 drawing, 164.70 × 109.20 actual vendor CAD |
| Body allowance | 0.50 per side at the three return strips relative to vendor CAD |
| OEM active area | 150.72 × 94.20, centered at X = −1.65 |
| Front aperture at Z = +2.30 | 154.048 × 97.975, centered at X = −1.65 and Y = +0.359 |
| Transition to original taper at Z = +1.10 | 152.583 × 96.196, centered at X = −1.65 and Y = +0.212 |
| Lip throat at Z = +0.53 | 151.48 × 95.18, centered at X = −1.65 and Y = +0.11, with R0.18 corners in plan |
| Glass-facing opening at Z = +0.35 | 151.68 × 95.38 at the throat center, with R0.28 corners in plan |
| Rear edge bevel | 0.10 radial × 0.18 axial |
| Glass-facing land and lip root | 1.05 flat land, then an outward taper to a root 2.30 from the throat edge at Z = +0.60 |
| Mounting | Four Ø3.60 through holes on 173.70 × 98.40 centers |
| OEM glass geometry | Layer 1 spans Z = −1.09 to 0, with the active layer modeled from Z = −0.50 to 0 |
| OEM lug geometry | Front at Z = −3.60, back at Z = −4.20, thickness 0.60 |
| Minimum installed clearance | 0.35 to the outer glass, 0.59 to the active glass solid, 0.29 to the approved surround, 2.21 to the closest front flex envelope |
| Lug bearing contact | 32.25 mm² on three lugs and 23.52 mm² on the relieved lower-left lug |

Only the inner aperture changed. The face, outer shape, and fastener surfaces match the approved fascia in the STEP comparison. The web remains at Z = +0.60 to +2.30 around the lip. The throat's straight edges extend about 0.02 mm over the inactive glass outline on the left, right and bottom. The top edge is farther out to accommodate the recorded eyes above the screen.

Exact solid intersections found zero installed interference with either glass layer, the OEM frame and lugs, the approved surround, and the checked flex envelopes. Contact is on the lug bearing pads at Z = −3.60. The full active rectangle plus 0.30 mm on each edge is clear from recorded eyes 226, 236 and 244 and along the screen normal. Eye 226 comes closest to the buffered viewing volume, clearing it by 0.0098 mm in nominal CAD.


## Shared hardware

| Qty | Part |
| ---: | --- |
| 4 | Fully threaded black M3 × 0.5 × 14 mm ISO 7380-1 button-head screws, measured under the head. Ø5.70 head, nominal 1.65 head height, 2 mm hex key. |
| 4 | DIN 433 M3 flat washers, Ø6 outer × Ø3.2 inner × 0.5 thick, black if available. |
| 4 | Existing M3 × 0.5 hex nuts, 5.50 across flats × 2.40 thick, in the approved side-loading pockets. |
| 1 | This fascia, printed in black ASA. |

The screw crosses the 0.50 washer, 5.90 fascia column, 0.60 lug and 3.00 front web before reaching the nut. An M3 × 8 ends 2.00 mm short of the nut. An M3 × 12 reaches only 2.00 mm into the 2.40 mm nut before counting tip chamfer. **M3 × 14 is the shortest suitable standard length for this stack.** It spans the full nut and projects 1.60 mm beyond it into the approved rear bore. The shortest modeled distance from a fitted tip to a hard stop behind it is 1.90 mm. The four heads sit proud at the corners on flat washers. [ISO 7380-1 supplier drawing](https://www.aspenfasteners.com/content/pdf/Metric_ISO_7380_spec.pdf) · [Example M3 × 14 specification](https://www.vital-parts.co.uk/hex-socket-button-head-screws-iso-7380-1/6955-hbs73801-m3-14-a2)

## Installation and removal

1. With the surround out of the car, clear the existing nut-loading slots and load the four retained nuts. Check the holes and bearing pads for print burrs. Seat the display on the existing four mount faces. Support it by the frame while the screws are out.
2. Offer up the fascia with the top tipped toward you about 10°. Guide the lower corners into position by reversing the removal motion below. The tapered corner belongs at viewer lower left. The four fascia pads should touch the metal lugs without screw force.
3. Fit a flat washer and shared screw at each corner. Start all screws by hand, then snug evenly. The washers should seat flat and the screen should remain clear of the fascia. Verify that the real display, print and hardware move freely on the bench before installing.
4. To remove, back out all four screws, lift the washers and support the LCD. Ease the **top** of the fascia toward you about 10° while easing the frame about 1 mm toward viewer-right. Raise it as you draw it out, then let it come back toward center once the lower corners pass the rail. Keep the frame roughly 10° tipped until the corners are clear. The 53 original poses and 25 samples across the tight interval cleared the surround, LCD and flex in CAD. The refined interval measured about 0.158 mm at the tightest point sampled, matching the approved fascia at that pose. A separate continuous check bounds fascia-to-base clearance at 0.080 mm or more along the interpolated CAD path. [Validation](validation.json) records angle and local X/Y/Z shifts about the Y = −52.7 pivot.
5. With the fascia off and the cables disconnected, remove the display along the approved path. Move it up 10 mm and out 20 mm together, then continue straight out. The base and retained nuts clear the conservative display sweep in nominal CAD.

## Print and reproduce

The offline Bambu Studio slice uses a P1S, 0.4 mm nozzle, Generic ASA, 0.20 mm layers, four walls and a 6 mm zero-gap outer brim. Print with the cosmetic face on the bed. The 182.74 × 112.10 mm footprint fits the plate with the brim. The released Bambu project was sliced from the revised mesh. The archived G-code has an aperture perimeter through the last lip layer at print Z = 2.0 mm and contains no support or bridge features. In the altered layers, the largest aperture road shift is 0.244 mm between 0.42 mm nominal outer-wall roads. The slice estimates **32 min 32 s** and **9.29 g**. No print or upload was started.

Check the as-printed clearance and removal path before tightening the screws. The 0.35 mm glass gap and the small removal clearance are nominal CAD dimensions. Shrinkage, warp, burrs, and installation variation still need a physical fit check.

[Release checkpoint and file hashes](checkpoint.json).

Keep this directory beside `upper_mount_revision`, `display_trim` and `extended_print_review`. The scripts use the approved geometry and prior trim for direct comparisons, and reuse the existing G-code parser. Use the Python at `/Users/adamgross/dev/artifacts/gauge-surround-2026-11-13/.venv/bin/python`. Run these scripts in order:

```text
src/build_trim.py
src/validate_trim.py
src/check_removal.py
src/render_trim.py
src/slice_trim.py
```

The build writes in display-local coordinates before transforming the installed part into the approved assembly position. The printable STL uses a rigid 180° rotation about display X.
