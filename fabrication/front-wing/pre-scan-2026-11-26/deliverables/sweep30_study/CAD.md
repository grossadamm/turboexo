# Experimental car-right 30° plan sweep

The lower guide sees the same inlet and first 80 mm as the approved design. Starting at car X = −116 mm, a cubic displacement turns the rear of the guide to 30° outboard in plan instead of 16°. The guide exits at X = −220 mm and Y = −537.174 mm, 10.074 mm farther outboard than the approved Y = −527.100 mm. X is car-forward and Y is car-left. The 36° vertical upsweep is independent of this plan angle.

The lower guide foot remains in place. Its inboard shoulder spreads toward the shifted crest to keep material above the unchanged curved underside. The wheel-side shelf gets narrower near the rear, but its height and the outer wing plan are retained. The upper blade follows the shifted crest, with no change in nominal width, rib chord, thickness, or 42° lower-surface exit elevation. Its five trailing-rib plan tangents range from 28.13° to 29.38°, rather than 30° throughout, because the blade ends 2–6 mm upstream of the guide’s 30° trailing plane.

- `wing_right.step` and `wing_right.stl` are the fused experimental part. The imported STEP is one valid solid, and the STL is one watertight volume.
- `blade_off_cad/wing_right.step` and `blade_off_cad/wing_right.stl` contain the same guide and shelf without the upper blade. `upper_blade.step` and `upper_blade.stl` are the isolated experimental blade for the solver. They are not standalone installed parts.
- `upper_blade_16_matched_width.stl` is the original approved blade retessellated with the candidate settings. No blade taper was necessary, so there is no new 16° geometry.
- `geometry_checks.json` records the CAD tangents, section checks, and source and output hashes. The original and candidate undersides coincided at all 1,977 sampled nonempty stations. The minimum checked vertical thickness in the aft shoulder was 3.375 mm over 672 stations. The isolated blade stayed inside the original plan with 2.00 mm minimum clearance from its boundary.

`build_sweep30.py` regenerates these files with the same CadQuery environment as the accepted work. The approved CAD and other vehicle components are untouched. This is a flow-screen candidate, without structural or installed-fit validation.
