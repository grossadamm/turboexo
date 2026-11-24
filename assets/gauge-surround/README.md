# Gauge surround: current matched release and print handoff

**2026-11-24: user confirmed the PLA bracket fit-test print was started in Bambu Handy.**
Do not submit another job automatically. Completion, removal and actual vehicle fit
have not been reported. This is not an ASA durability validation.

## Current files

- `display_trim_flush/surround.step` / `surround.stl`: final matched base bracket.
- `display_trim_flush/display_trim.step`: final flush fascia with the soft glass lip.
- `display_trim_flush/display_trim_face_down.stl`: fascia in print orientation.
- `display_trim_flush/display_trim_assembly.step` / `.3mf`: installed assembly for
  inspection; do not print the device/reference geometry.
- `display_trim_flush/surround_P1S_ASA.3mf`: prepared ASA base project (9 h 16 min,
  264.39 g); NOT the PLA test job now running.
- `display_trim_flush/display_trim_P1S_ASA.3mf`: prepared ASA fascia project
  (36 min 35 s, 11.78 g). Fascia has not been reported printed.
- `pla_test_draft/TurboExo_Bracket_TEST_PLA_2wall_028.gcode.3mf`: exact uploaded
  PLA base fit-test job, user reported started. 2 walls, 0.28 mm layers (0.20 first),
  15% infill, P1S 0.4 mm nozzle, textured PEI, Generic PLA 220 C nozzle / 55 C bed,
  55 degree tilt, snug supports and the preserved local support exclusions.
  Estimate: 8 h 13 min 12 s, 280.28 g PLA.
- `pla_test_draft/upload_receipt.json`: remote readback SHA-256 matched the local
  job. Hash: `5abf493faa5b24fedefc7d792d43e583cede2abb04c2d12512a70f04fa71880a`.
- `display_trim_flush/assembly_view.html`: interactive depth-buffered assembly.
  Open locally or use the T3 HTML renderer; images are archived alongside it.

**Use the base and fascia from `display_trim_flush` together.** Earlier base and
trim directories are dependencies/evidence, not alternative files to print.
See [handoff](../../docs/GAUGE_SURROUND_HANDOFF.md) for decisions, hardware and next actions.

## Rebuild and editing

Install Git LFS and run `git lfs pull` after cloning. CAD, meshes, projects and
photos are LFS objects; JSON/source/notes remain ordinary Git content.

The geometry source dependency chain is intentionally retained:

1. `upper_mount_revision/src/surround.py` generates the underlying one-piece base
   from the measured roof/display/vehicle datums in its `inputs/`.
2. `display_trim_flush/src/build_trim.py` generates the latest fascia and adds the
   matched seam-backing lands to that base.
3. `display_trim_soft_lip` is the immutable regression reference used to prove the
   accepted glass lip was preserved. Do not edit it to make a validation pass.

Use Python 3.11 with CadQuery 2.8, NumPy, SciPy and trimesh. Rendering also uses
Matplotlib, Pillow and VTK. The original local working interpreter was
`/Users/adamgross/dev/artifacts/gauge-surround-2026-11-13/.venv/bin/python`.

```sh
python -m pip install -r assets/gauge-surround/requirements.txt
python assets/gauge-surround/rebuild.py --output /tmp/surround-rebuild --validate
```

The archived source was rebuilt in a separate directory on 2026-11-24.
`portable_rebuild_check.json` records zero added/removed volume for both final
parts compared with the released STEP files.

The output path must not already exist; archived release files remain untouched.
Validation scripts use only archived geometry/data, not credentials or the printer.
The exact released 3MFs contain the process, geometry, modifiers and sliced G-code.
For a changed model, update and re-slice in Bambu Studio; do not send stale G-code.
Historical `slice_*` scripts inside the immutable soft-lip reference depend on the
original external working tree. They are retained to preserve its source manifest,
not as the supported portable slicing entry point. Do not confuse CAD validation
with physical fit or fatigue certification.

`SHA256SUMS.json` records archived release payloads, prior to these handoff notes.
Original scratch iterations remain at
`/Users/adamgross/dev/artifacts/gauge-surround-design-2026-11-21/`; no API logs,
printer credentials, environment directories or live launch scripts are committed.
