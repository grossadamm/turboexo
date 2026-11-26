# Rebuild or verify the Closed42 car-right draft fit project

The two input STLs are full-scale and already in bed orientation. The script keeps their geometry and orientations. It only places the inner STL at X128 Y132.4 and the outer STL at X128 Y128 on their respective plates. It inherits the P1S 0.4 mm Generic PLA settings from `fabrication/front-wing/fold70-2026-11-23/deliverables/fold70/right_fit/right_fit_draft_pla_p1s.3mf` in the project repo. The outer object overrides support type to normal with critical-only 25° threshold and 0.30 mm XY clearance. The inner object retains the inherited tree-slim support settings.

Set `FOLD70_PLA` to that reference 3MF and run from this directory. This recipe requires Python 3 and Bambu Studio 02.09.01.70. It slices offline only.

```sh
build=$(mktemp -d)
mkdir "$build/first" "$build/reopen"
bambu=/Applications/BambuStudio.app/Contents/MacOS/BambuStudio
python3 closed42_fit_slicer.py --outer-settings outer_support_override.json \
  "$FOLD70_PLA" .. "$build/input.3mf"
"$bambu" --outputdir "$build/first" --arrange 0 --orient 0 --slice 0 \
  --export-3mf trial.3mf "$build/input.3mf"
"$bambu" --outputdir "$build/reopen" --arrange 0 --orient 0 --slice 0 \
  --export-3mf closed42_right_fit_draft_pla_p1s.3mf "$build/first/trial.3mf"
project="$build/reopen/closed42_right_fit_draft_pla_p1s.3mf"
python3 closed42_fit_gcode_qa.py "$project" > "$build/toolpaths.json"
python3 closed42_fit_verify_project.py "$project" .. "$build/first/result.json" \
  "$build/reopen/result.json" "$build/toolpaths.json"
python3 closed42_fit_features_qa.py "$project" feature_probe_coordinates.txt \
  --blade-probe blade_tip_probe_coordinates.json
python3 closed42_fit_blade_tip_coverage.py "$project" blade_tip_probe_coordinates.json
```

Project and G-code hashes include slicer-generated metadata and can differ across independent rebuilds. The verifier checks source-geometry correspondence, actual embedded G-code, expected settings, native per-plate previews, and zero deposited envelope violations against the build volume and exclusion rectangle. It does not simulate the physical printer or validate a printed piece. Remove the outer plate’s accessible runner-gap support and clear the lower mouths of the inner B/E bores before fit testing.
