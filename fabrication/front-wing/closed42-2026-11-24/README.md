# Closed bumper joint and 42° front wings

Open [the offline viewer](deliverables/closed42_joint/rotate.html) and choose **Left joint** or **Right joint** to inspect the revised chin and compressed gasket. Both faired outer wings have the 36° floor and 42° upper blade. All CAD parts share the original car frame in millimetres. The GLB uses metres and Y up.

## Restore the CAD

Run these commands from this directory after checkout. Both archives are ordinary Git files.

```sh
shasum -a 256 -c SHA256SUMS
tar -xJf approved-cad.tar.xz
tar -xJf design-inputs.tar.xz
python3 - <<'PY'
import hashlib, json
from pathlib import Path
for files in json.loads(Path('archive_contents.json').read_text()).values():
    for name, record in files.items():
        path = Path(name)
        assert path.stat().st_size == record['bytes'], name
        assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], name
PY
```

The approved archive contains the 160-component installed STEP, standalone chin, installed-shape seal, both wings, component STLs, and the viewer GLB. Open `deliverables/closed42_joint/installed_mm.step` for the full assembly. The second archive contains the upstream CAD and display inputs used by the generators.

## Rebuild

Use the project's CAD environment with CadQuery 2.8, NumPy, SciPy, trimesh, shapely and rtree. The saved outputs above preserve the reviewed revision exactly. Run regeneration in a disposable copy because the scripts write to the same paths as the saved outputs.

```sh
python code/faired42_wing.py
python code/closed42_joint.py
python code/package_closed42_joint.py deliverables/closed42_joint/chin.step deliverables/closed42_joint/seal.step
python code/closed42_viewer.py --part chin deliverables/closed42_joint/chin.step --part seal deliverables/closed42_joint/seal.step
```

The viewer builder uses the saved template and full-assembly image. Baseline assembly and mesh inputs are frozen at the revision used for this closure. The manufacturing CAD and the lightweight viewing mesh are separate exports.

## Verification recorded with the design

The [joint checks](deliverables/closed42_joint/joint_checks.json) cover 1,239 sampled contacts between the rigid chin, seal, and V9 bumper surface. The gasket spans Y −344 to +363 mm. It tapers toward each end, where the chin leaves the bumper toward the wheel. The [assembly audit](deliverables/closed42_joint/assembly_release.json) checks the reopened assembly. The tires are reference envelopes. Physical fit, free gasket thickness, structural capacity, and aerodynamic performance remain unverified.
