"""Generate a car-right 30-degree plan-sweep candidate without touching the release."""

from hashlib import sha256
import argparse
from inspect import getsource
from math import atan, degrees, radians, sqrt, tan
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import json
import sys

import cadquery as cq
import numpy as np
import trimesh


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "code"))
import faired42_wing as faired
import layered_channel_wing as layered
import swept_ramp_wing as swept
from twin_spar_wing import heights, intersector


SIDE = "right"
TIP = abs(swept.WHEEL_Y[SIDE])
EXIT_DEG = 30.0
BLEND_X = swept.START-80.0
BLEND_RUN = BLEND_X - swept.TAIL_X
EXIT_SLOPE_DELTA = tan(radians(EXIT_DEG)) - tan(swept.EXIT_TANGENT)
RIBS = (0.0, 0.25, 0.5, 0.75, 1.0)


def crest_outboard(x, variant=True):
    # Keep the complete forward 80 mm on the accepted circle. Ramp the added
    # outward slope quadratically through the remaining run, giving a C2
    # join to that circle and exactly 30 degrees at the trailing plane.
    base = TIP - swept.EXIT_INSET + sqrt(swept.RADIUS**2-swept.RUN**2) - sqrt(swept.RADIUS**2-(swept.START-x)**2)
    if not variant:
        return base
    t = max(0.0, (BLEND_X-x)/BLEND_RUN)
    return base + EXIT_SLOPE_DELTA*BLEND_RUN*t**3/3.0


def crest_slope_rearward(x):
    d = swept.START-x
    return d/sqrt(swept.RADIUS**2-d**2) + EXIT_SLOPE_DELTA*max(0.,(BLEND_X-x)/BLEND_RUN)**2


def mapped_profile_y(x, y, crest, width, tip):
    # Move the crest and drop to the shelf together, but pin the inboard
    # foot and outer edge. Stretching the inboard shoulder keeps top skin
    # over the retained lower fascia instead of sweeping away its stock.
    delta = crest_outboard(x) - crest_outboard(x, False)
    if y <= crest:
        t = (y-crest+width)/width
        return y + delta*t**3*(10-15*t+6*t*t)
    if y < crest+18.0:
        return y + delta
    return y + delta*(tip+2.0-y)/(tip+2.0-crest-18.0)


def rescope(function, variables, replacements=()):
    """Reuse the source CAD routine and fail if an expected edit stops matching."""
    script = getsource(function)
    for old, new in replacements:
        assert script.count(old) == 1, old
        script = script.replace(old, new)
    namespace = function.__globals__.copy()
    namespace.update(variables)
    exec(compile(script, function.__code__.co_filename, "exec"), namespace)
    return namespace[function.__name__]


def geometry_functions():
    profile = rescope(swept.profile, {"mapped_profile_y": mapped_profile_y}, ((
        "return cq.Vector(x, SIGNS[side]*y, z)",
        "return cq.Vector(x, SIGNS[side]*mapped_profile_y(x, y, crest, inboard_width, tip), z)",
    ),))
    wing = rescope(swept.build, {"profile": profile})
    rib = rescope(layered.rib,
        {"crest_outboard": crest_outboard, "crest_slope_rearward": crest_slope_rearward}, (
        ("crest = abs(WHEEL_Y[side])-58+sqrt(RADIUS**2-RUN**2)-sqrt(RADIUS**2-(START-x)**2)",
         "crest = crest_outboard(x)"),
        ("dcrest_dx = (START-tail)/sqrt(RADIUS**2-(START-tail)**2)",
         "dcrest_dx = crest_slope_rearward(tail)"),
    ))
    swept_variant = SimpleNamespace(**(vars(swept) | {"build": wing}))
    control = rescope(faired.generate, {"swept": swept_variant}, ((
        "    result = result.fuse(upper_blade(side)).clean()\n", "",
    ), (
        "building the unchanged upper shell", "building the progressively swept upper shell",
    ),))
    return rib, control


def validated_mesh(shape, path):
    assert shape.isValid() and len(shape.Solids()) == 1 and shape.Volume() > 0, path
    shape.exportStl(str(path), tolerance=.018, angularTolerance=.06, relative=False)
    mesh = trimesh.load_mesh(path)
    assert mesh.is_volume and mesh.body_count == 1, path
    assert abs(mesh.volume / shape.Volume(1e-8) - 1.0) < .005, path
    return {"triangles": len(mesh.faces), "volume_mm3": float(mesh.volume)}


def pack_blade(rib):
    wires = [rib(SIDE, f, 42) for f in RIBS]
    sides = cq.Solid.makeLoft(wires).Faces()
    caps = [cq.Face.makeNSidedSurface(wire.Edges(), []) for wire in (wires[0], wires[-1])]
    return cq.Solid.makeSolid(cq.Shell.makeShell(sides+caps)).fix()


def validate_unchanged(control, baseline):
    # Check the unchanged lower fascia, inboard/root surfaces and internal
    # surfaces beneath the original plate-facing top skin. Vertical sections
    # may have multiple intervals for the print cavities and spar sockets.
    b, v = intersector(baseline), intersector(control)
    lower, inboard = [], []
    for x in np.r_[np.linspace(-219.0, -211., 8), np.linspace(-210.,12.,45)]:
        for y in np.linspace(437.0, TIP-.15, 52):
            hb, hv = heights(b, x, -y), heights(v, x, -y)
            if hb and hv:
                lower.append(abs(hb[0]-hv[0]))
                if y < 465.0 or x > swept.START:
                    assert len(hb) == len(hv), (x, y, hb, hv)
                    inboard.extend(np.abs(np.array(hb)-np.array(hv)).tolist())
            else:
                assert bool(hb) == bool(hv), (x, y, hb, hv)
    assert max(lower) < .01 and max(inboard) < .01, (max(lower), max(inboard))

    # The aft outboard transition must not open through the underside or
    # become an unprintably thin strip as the guide crest moves outward.
    thickness = []
    for x in np.linspace(-219.94, -210., 16):
        for y in np.linspace(479., 525., 42):
            hv = heights(v, x, -y)
            assert len(hv) == 2, (x, y, hv)
            thickness.append(hv[-1]-hv[0])
    assert min(thickness) >= 2.4, min(thickness)

    # Shelf heights stay fixed outside the shortened transition. Compare
    # stations that lie on both the baseline and candidate flat shelf.
    shelf_samples = []
    for x in (-105., -145., -175., -195., -207., -212., -216., -219.0):
        for offset in (-8., -6., -4., -2.):
            y = TIP+offset
            hb, hv = heights(b, x, -y), heights(v, x, -y)
            if hb and hv:
                shelf_samples.append(abs(hb[-1]-hv[-1]))
    assert max(shelf_samples) < .007, max(shelf_samples)
    return {"matched_lower_section_count": len(lower), "max_underside_delta_mm": max(lower),
            "aft_inboard_shoulder_thickness_sample_count": len(thickness),
            "minimum_sampled_aft_shoulder_thickness_mm": min(thickness),
            "max_inboard_or_forward_section_delta_mm": max(inboard),
            "common_shelf_samples": len(shelf_samples), "max_shelf_height_delta_mm": max(shelf_samples)}


def actual_exit_tangents(control):
    # Locate the end of the rail's exact CAD crest edge, not a finite
    # difference of the mesh or the formula from which the loft was built.
    p = cq.Vector(swept.TAIL_X, -crest_outboard(swept.TAIL_X),
                  layered.shelf(swept.TAIL_X)+faired.matched.CROWN_ABOVE_SHELF)
    matches = []
    for edge in control.Edges():
        for u, point in ((0, edge.startPoint()), (1, edge.endPoint())):
            if (point-p).Length > 0.008: continue
            tan = edge.tangentAt(u)
            if abs(tan.x) < .50: continue
            matches.append({"point_car_xyz_mm": list(point.toTuple()),
                            "outward_angle_deg": degrees(atan(tan.y/tan.x)),
                            "upsweep_angle_deg": degrees(atan(-tan.z/tan.x))})
    assert matches and max(abs(v["outward_angle_deg"]-EXIT_DEG) for v in matches) < .03, matches
    return matches


def blade_exit_tangents(rib):
    out = []
    for f in RIBS:
        aft = -218.0+4.0*f*f
        def lower_end(fn):
            choices = []
            for edge in fn(SIDE, f, 42).Edges():
                for u, p in ((0,edge.startPoint()),(1,edge.endPoint())):
                    if abs(p.x-aft) < .001 and abs(edge.tangentAt(u).x) > .4:
                        choices.append((p, edge.tangentAt(u)))
            p, tangent = min(choices, key=lambda item:item[0].z)
            return p, degrees(atan(tangent.y/tangent.x)), degrees(atan(-tangent.z/tangent.x))
        pb, yb, zb = lower_end(layered.rib)
        pv, yv, zv = lower_end(rib)
        assert abs(zv-42.0) < 1e-8 and abs(zb-42.0) < 1e-8
        assert abs(pv.z-pb.z) < 1e-8
        out.append({"rib_fraction": f, "blade_lower_exit_upsweep_deg": zv,
                    "blade_lower_exit_outward_deg_baseline": yb,
                    "blade_lower_exit_outward_deg_variant": yv,
                    "blade_lower_exit_car_xyz_mm": list(pv.toTuple()),
                    "blade_lower_exit_outward_displacement_mm": pb.y-pv.y})
    return out


def measure_diagnostic(rib, proof):
    # No taper was needed, so this is geometrically identical to the
    # accepted 16-degree blade, re-tessellated using the candidate settings.
    p = HERE / "upper_blade_16_matched_width.stl"
    baseline = faired.upper_blade(SIDE)
    proof["blade"]["section_rib_trailing_edge_measurements"] = blade_exit_tangents(rib)
    proof["blade"]["diagnostic_matched_width_baseline"] = {
        "file": p.name,
        "geometry": "Exact accepted 16-degree blade; no width change on either case.",
        "source": "code/faired42_wing.py: upper_blade('right')",
        **validated_mesh(baseline, p),
        "sha256": sha256(p.read_bytes()).hexdigest(),
    }
    outputs = (HERE / "wing_right.step", HERE / "wing_right.stl", HERE / "upper_blade.step",
               HERE / "upper_blade.stl", HERE / "blade_off_cad/wing_right.step",
               HERE / "blade_off_cad/wing_right.stl")
    proof["sha256_candidate_outputs"] = {str(p.relative_to(HERE)): sha256(p.read_bytes()).hexdigest() for p in outputs}
    (HERE / "geometry_checks.json").write_text(json.dumps(proof, indent=2)+"\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--measure-existing", action="store_true", help="Add blade tangent and output traceability data without regenerating candidate CAD.")
    opts = parser.parse_args()
    rib, build_control = geometry_functions()
    if opts.measure_existing:
        measure_diagnostic(rib, json.loads((HERE / "geometry_checks.json").read_text()))
        return
    control_dir = HERE / "blade_off_cad"
    control_dir.mkdir(exist_ok=True)
    with TemporaryDirectory() as temporary:
        build_control(SIDE, Path(temporary), control_dir)
    control = swept.read(control_dir / "wing_right.step")
    blade = pack_blade(rib)
    plan = swept.wing_plan(SIDE)
    # Prism covers the full z range of the blade. An exactly empty subtract
    # verifies against the CAD outline including its rounded rear corner.
    excess = blade.cut(plan)
    assert excess.Volume() < 1e-5, excess.Volume()
    plan_margin = min(blade.distance(face) for face in plan.Faces())
    assert plan_margin > 1.0, plan_margin
    blade_path = HERE / "upper_blade.step"
    cq.exporters.export(blade, str(blade_path))
    blade = swept.read(blade_path)
    blade_check = validated_mesh(blade, blade_path.with_suffix(".stl"))

    print("variant blade ready; fusing the printable assembly", flush=True)
    assert blade.intersect(control).Volume() > 1.
    result = control.fuse(blade).clean()
    assert result.isValid() and len(result.Solids()) == 1
    final_path = HERE / "wing_right.step"
    cq.exporters.export(result, str(final_path))
    result = swept.read(final_path)
    final_check = validated_mesh(result, final_path.with_suffix(".stl"))

    src = HERE.parent / "cfd_corner_study/blade_off_cad/wing_right.step"
    baseline = swept.read(src)
    proof = {
        "coordinate_frame": "Car-frame millimetres, X forward, Y car-left, Z up.",
        "crest_inlet_car_xy_mm": [swept.START, -crest_outboard(swept.START)],
        "crest_inlet_tangent_deg": 0.,
        "crest_blend_start_car_xy_mm": [BLEND_X, -crest_outboard(BLEND_X)],
        "baseline_crest_outlet_car_xy_mm": [swept.TAIL_X, -crest_outboard(swept.TAIL_X, False)],
        "baseline_crest_design_exit_deg": degrees(swept.EXIT_TANGENT),
        "variant_crest_outlet_car_xy_mm": [swept.TAIL_X, -crest_outboard(swept.TAIL_X)],
        "variant_crest_exit_cad": actual_exit_tangents(control),
        "variant_exit_outward_displacement_mm": crest_outboard(swept.TAIL_X)-crest_outboard(swept.TAIL_X, False),
        "lower_guide_cross_section": "Original inboard foot and outer plan held fixed. The inboard shoulder spreads toward the new crest to keep skin continuous above the unchanged underside; the wheel-side shelf narrows by the crest shift. Upper control-point heights are unchanged.",
        "blade": {"narrowing_rule": "None. Both the original rib offsets and relative X/Z rib profiles are retained.",
                   "minimum_distance_to_original_plan_boundary_mm": plan_margin,
                   "stray_volume_beyond_plan_mm3": excess.Volume(),
                   "control_overlap_mm3": blade.intersect(control).Volume(1e-8),
                   **blade_check},
        "fused": final_check,
        "unchanged_sections": validate_unchanged(control, baseline),
        "sha256_sources": {str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest() for p in
                           (Path(faired.__file__), Path(swept.__file__), Path(layered.__file__), src,
                            HERE.parent / "faired42_wing/wing_right.step")},
    }
    measure_diagnostic(rib, proof)
    print(json.dumps(proof, indent=2), flush=True)


if __name__ == "__main__":
    main()
