# Recovery and rebuild scope

This is the 2026-11-26 pre-scan experimental state, not an approved manufacturing release. The saved `deliverables/sweep30_duct_study/rotate.html` and `inline.html` embed the combined viewing model and can be opened offline; the GLB and the underlying study CAD are also saved. The passenger scoop is a switchable mirror registered to the bracket datums. Its interference report identifies several collisions. Keep the saved outputs unchanged and work in a disposable copy when rebuilding.

The checkpoint mirrors the artifact-root paths. For the older closed42 inputs, overlay the preceding repository checkpoint in the same disposable root: copy `../closed42-2026-11-24/code/` and its `grid/plate_v2.json`, then extract that checkpoint's `approved-cad.tar.xz` and `design-inputs.tar.xz` there. Check its `SHA256SUMS` first and follow its README and `archive_contents.json` to verify extracted members. These archives include `deliverables/faired42_wing/wing_right.step` and `deliverables/skin_first_wing/wing_right.step`; the latter supplies the baseline geometry for the sweep builder. The accepted right-wing STEP in the approved archive hashes to `a5cfc601afc3de20cbb5d60bd13c242d73cae7c62e716f5d1eade7cd850854d7`, matching this study's `geometry_checks.json`. The four direct imported wing modules in that prior checkpoint match the study's source files byte for byte.

## Rebuild the study geometry and combined viewer

The following commands assume the disposable overlay described above, with this checkpoint copied on top. CAD regeneration requires a compatible Python environment with CadQuery/OCP, NumPy, SciPy, trimesh, shapely and rtree. The progressive scoop also needs a trimesh-compatible Manifold boolean backend (`manifold3d`). The saved STEP, STL, GLB and HTML are the reference outputs. Regeneration may change export headers or mesh ordering.

```sh
python deliverables/sweep30_study/build_sweep30.py
python duct_progressive_turn/design.py
python deliverables/sweep30_duct_study/assemble.py deliverables/sweep30_duct_study/right_pose.txt
```

The sweep script builds the experimental right-wing STEP and upper blade and checks against the saved `deliverables/cfd_corner_study/blade_off_cad/wing_right.step`. It also uses the accepted STEP from the prior archive. The scoop script computes a mesh union from `scoop_green_roof/green_roof.stl` and a generated extension. It executes only the portion of `scoop_smooth_deck/build.py` before `def wire(t):`, which reads `grid/inboard_mounts_v4_geometry.json`; those three inputs are preserved here. The full upstream green-roof design history and the inlet-form STEP needed to regenerate the original scoop itself are outside this checkpoint. The scoop result is an STL mesh, not a newly generated STEP.

The combined-viewer assembly takes the **saved** `deliverables/sweep30_study/render_front.glb` and `rotate.html`, the progressive scoop STL and the saved `right_pose.txt`; it writes a new combined GLB, HTML pages and `assembly.json`. Rebuilding the sweep STEP alone does not regenerate its source GLB or the fallback image. The original base meshes are preserved by the assembly script; registration and its residuals are recorded in `right_registration.json`. The separate `duct_progressive_turn/viewer.py` compares against an earlier outboard study and needs additional upstream assets not included here; use the saved `Progressive_brake_scoop.html` for that view.

CFD study outputs and raw snapshots are preserved as evidence of the exploratory runs. This checkpoint does not establish a fully reproducible solver environment, identical CFD reruns, vehicle scan fit, structural performance or road safety. Treat the CFD results as comparative study evidence, not validated aerodynamic predictions.
