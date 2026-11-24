# Fold70 CAD checkpoint — 2026-11-23

This is the completed 70 mm center-lead, R120 plan-trim styling study from
`~/dev/artifacts/front-wing-2026-11-20`. It preserves the original car-frame
millimetres and original `code/`, `grid/`, and `deliverables/` structure.
It records modeled geometry, not confirmation of physical fit or fabrication readiness.

Open `deliverables/fold70/fold70_viewer.html` directly in a browser for the
self-contained view sheet and draggable orbit. The actual new part is
`deliverables/fold70/full_folded_chin_mm.step`; datums and original assembly QA
are alongside it. `checkpoint_geometry_check.json` records an independent STEP
reimport: valid, one solid, using CadQuery 2.8.0.

## Recover the installed assembly and regeneration inputs

`cad-inputs.tar.xz` is a lossless, ordinary Git blob with seven original CAD
files. It includes the final `deliverables/fold70/installed_mm.step` (146 assembly
leaves according to the original `assembly_check.json`), the prior installation,
seal, fiberglass STEP/STL, V9 hardware 3MF, and source corner STEP. The archive
preserves relative paths. `archive_contents.json` records each uncompressed
file's byte count and SHA-256. Every archived member was read back and compared
to the original before committing. `SHA256SUMS` covers all other checkpoint
files, including the archive. No LFS server is required to recover these CAD files.

From this directory:

```sh
shasum -a 256 -c SHA256SUMS
tar -xJf cad-inputs.tar.xz
python3 - <<'PY'
import hashlib, json
from pathlib import Path
for name, record in json.loads(Path('archive_contents.json').read_text()).items():
    data = Path(name).read_bytes()
    assert len(data) == record['bytes'], name
    assert hashlib.sha256(data).hexdigest() == record['sha256'], name
print('All seven restored CAD files match their original bytes.')
PY
```

The final assembly SHA-256 can also be compared directly to
`deliverables/fold70/assembly_check.json`. Keep the compressed archive even after
extracting; extracted large dependencies are ignored locally to prevent accidental
ordinary Git staging.

## Regenerate

Create a Python environment with `cadquery`, `numpy`, `scipy`, `trimesh`, and
`Pillow`. The original geometry environment reported CadQuery 2.8.0, NumPy 2.4.6,
SciPy 1.17.1, trimesh 5.2.1, and Pillow 13.0.0. Original rendering used NumPy 2.5.5
and SciPy 1.18.1 in a separate environment; exact rendering equivalence across
versions is not promised.

After extracting the archive, run from this directory:

```sh
python code/fold70.py
python code/fold70_install.py
cc -O3 -shared -fPIC code/scan_raster.c -o /tmp/fw_scan_raster.dylib
python code/fold70_cad_views.py
python code/fold70_orbit_views.py
python code/fold70_viewer.py
```

The renderer loads `/tmp/fw_scan_raster.dylib`, matching its original macOS
workflow. Set `CAD_PYTHON` if STEP tessellation needs a separate CadQuery Python.
The copied renderer imports the local `step_mesh.py` helper instead of the
unrelated historical preview stack; its tessellation command is preserved.
All other copied source files are byte-identical to their artifact originals.
`package_front_v4.py` is included for the assembly `leaves` helper only;
regenerating the unrelated V4 design and predecessor geometry is outside this
checkpoint. Their required final geometry is included as exact input CAD.

The final chin's independent STEP reimport and archive byte checks were run;
a complete geometry or image regeneration was not run during checkpointing.
