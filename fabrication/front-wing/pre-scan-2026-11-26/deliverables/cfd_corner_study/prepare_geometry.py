"""Pack right-front screen geometry from the accepted installed CAD and meshes."""
from hashlib import sha256
from pathlib import Path
import json
import sys

import cadquery as cq
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
D = HERE.parent
sys.path.insert(0, str(ROOT / "code"))
import faired42_wing

KEYS = {}
INFO = {"solver_axes": {"x": "-carX (rearward)", "y": "-carY (outboard)", "z": "carZ (up)"}, "units": "mm"}
ORIGINS = {}


def origin(path):
    name = str(path.relative_to(ROOT))
    if name not in ORIGINS:
        ORIGINS[name] = sha256(path.read_bytes()).hexdigest()
    return name


def mesh(name, m, path, crop=False, note=None):
    v = np.asarray(m.vertices, np.float32) * [-1, -1, 1]
    faces = np.asarray(m.faces, np.int32)
    if crop:
        faces = faces[np.max(v[faces, 1], axis=1) >= -0.5]
        if not len(faces):
            return
        v_idx, remapped = np.unique(faces, return_inverse=True)
        v, faces = v[v_idx], remapped.reshape(faces.shape)
    KEYS[name + "_v"] = v.astype("<f4")
    KEYS[name + "_f"] = faces.astype("<i4")
    INFO[name] = dict(source=origin(path), triangle_count=len(faces), mesh_bounds_in_solver_mm=[v.min(0).tolist(), v.max(0).tolist()])
    if note:
        INFO[name]["note"] = note


def load(path):
    return cq.importers.importStep(str(path)).val()


def tri(shape, tol=0.065, angle=0.08):
    verts, faces = shape.tessellate(tol, angle)
    return trimesh.Trimesh(np.array([v.toTuple() for v in verts]), faces, process=False)


def main():
    on_source = D / "faired42_wing/wing_right.step"
    off_source = HERE / "blade_off_cad/wing_right.step"
    blade_source = ROOT / "code/faired42_wing.py"
    blade = faired42_wing.upper_blade("right")
    off = load(off_source)
    on = load(on_source)
    fused = off.fuse(blade).clean()
    assert fused.isValid() and len(fused.Solids()) == 1
    assert abs(on.Volume(1e-8) - fused.Volume(1e-8)) < 0.005
    INFO["wing_equivalence"] = {"control_and_blade_fused_mm3": fused.Volume(1e-8),
        "control_mm3": off.Volume(1e-8), "approved_full_mm3": on.Volume(1e-8),
        "accepted_full_source": origin(on_source),
        "method": "Control from accepted generator with precisely one final blade union removed. Exact standalone blade from the same generator; separate mask is OR-ed into the common control to avoid noise from independent voxelizations outside the blade. Re-fused control and blade checked valid with one solid and compared to accepted STEP by volume."}
    mesh("wing_control", trimesh.load_mesh(off_source.with_suffix(".stl")), off_source.with_suffix(".stl"),
        note="Audited STL of source-generated pre-blade solid. Vertical envelope seals plate-facing lightening cavities and spar pockets only.")
    mesh("upper_blade", tri(blade, 0.035, 0.06), blade_source,
        note="Exact isolated 42 degree design blade before union with common wing. Rib-geometry source: code/layered_channel_wing.py.")
    origin(ROOT / "code/layered_channel_wing.py")
    origin(off_source)

    path = D / "front_end_v9/fiberglass_v9_mm.step"
    mesh("bumper", tri(load(path), .12, .09), path, crop=True,
        note="Right exterior derived by first x-ray hit of V9 fiberglass mesh. Occupancy continues to common planar aft closure at x=339.2 mm; grille openings are left clear where no fiberglass intersects the ray.")
    path = D / "closed42_joint/chin.stl"
    mesh("chin", trimesh.load_mesh(path), path, crop=True, note="Same installed rigid chin in both configurations.")
    path = D / "closed42_joint/seal.stl"
    mesh("seal", trimesh.load_mesh(path), path, crop=True, note="Same thin compressed seal in both configurations.")
    path = D / "bracket/inboard_mounts_v4_mm.step"
    right = sorted((s for s in load(path).Solids() if s.Center().y < 0), key=lambda s: s.Volume(), reverse=True)
    assert len(right) == 2
    for name, shape in zip(("green_web", "green_brace"), right):
        mesh(name, tri(shape), path)
    path = D / "skin_first_wing/plate_right.stl"
    mesh("green_plate", trimesh.load_mesh(path), path,
        note="Released outer plate from the same assembly; obsolete mount rail, add-on receivers and spars excluded.")
    path = D / "outboard_wing_study/assets/tire_car_right_inferred_envelope_mm.obj"
    mesh("tire", trimesh.load_mesh(path), path,
        note="Inferred straight-ahead right tire envelope, not measured production tread or sidewall. Vertical exterior envelope fills the wheel/rim center. No tread, rotation, steering, camber, or contact deformation.")
    origin(path.with_name("tire_context_provenance.json"))

    # Occupy the nominal depth of the actual center cores, not an arbitrary
    # upstream blanking plate. Tank envelopes here are the original CAD solids.
    for package in ("intercooler", "radiator"):
        path = D / f"body/{package}_v4_mm.step"
        for i, s in enumerate(load(path).Solids()):
            mesh(f"{package}_{i}", tri(s, .15, .12), path, crop=True)
    INFO["sources_sha256_relative_to_artifact_root"] = ORIGINS
    np.savez_compressed(HERE / "geometry_meshes.npz", **KEYS)
    (HERE / "geometry_provenance.json").write_text(json.dumps(INFO, indent=2) + "\n")
    print(json.dumps(INFO["wing_equivalence"], indent=2), flush=True)
    print("cached meshes", len(KEYS)//2, flush=True)


if __name__ == "__main__":
    main()
