# Car-right bracket-to-fiberglass fit print

Open **`right_fit_draft_pla_p1s.3mf`** in Bambu Studio for the full-scale right end of the 70 mm folded chin. The single rigid part runs from the uncut car-right plate to a section at Y = −260 mm. It includes the B/E mounting flange and 45 mm of the central seal seating band. The compliant seal is a separate component and is omitted from this print. Use this draft on the stationary car to check the hole alignment, brace clearance and fiberglass joint.

The Generic PLA project uses 220°C nozzle and 55°C textured PEI, with 0.28 mm layers, two walls, two top/bottom layers, 3% gyroid, tree supports and a 5 mm brim. The reopened project sliced in Bambu Studio at 5 h 48 min and 138 g. Geometry and placement match the independently verified fit section.

The earlier ASA project includes the oriented geometry, embedded toolpath and draft settings for a 0.4 mm nozzle and the project’s calibrated ASA on textured PEI. The flange is on the bed. The slice uses 0.28 mm layers, two walls, two top and bottom layers, 3% gyroid, critical-region tree supports from the build plate and a 5 mm brim. Bambu Studio 2.9.1.70 estimated 6 h 25 min and 120 g including supports. The printer-side pressure advance setting and actual fit are unverified.

`right_fit_car_mm.step` is in the installed car frame. `right_fit_bed_mm.stl` is oriented for slicing. `extraction.json` records the source hash and rigid transform. The independent CAD checks and the slicer and toolpath reports are alongside the project. To regenerate the section from the committed STEP, run `python extract_right_fit.py` with CadQuery, NumPy, SciPy, trimesh and Shapely.
