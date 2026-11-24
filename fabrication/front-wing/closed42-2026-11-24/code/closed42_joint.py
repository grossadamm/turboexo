"""Fit the swept upper chin returns and compressed seal to the installed V9 shell.

Car frame in mm: X forward, Y left, Z up. Only the three connected faces at
the top of the Fold70 wall are refaired. Their lower boundaries are fixed.
"""

import hashlib
import json
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from OCP.BRep import BRep_Tool
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.BRepTools import BRepTools
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt, gp_Vec
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from scipy.interpolate import BSpline, CubicSpline, PchipInterpolator
from scipy.ndimage import gaussian_filter1d

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "deliverables"
OUT = D / "closed42_joint"
CHIN = D / "skin_first_wing/chin.step"
GLASS = D / "front_end_v9/fiberglass_v9_mm.step"
# The aft tips finish about 5 mm behind the wing trim, near X=-225.
# Right and left have different Y coordinates in the survey frame.
ENDS = {-1: 344.0, 1: 363.0}
STARTS = {-1: 263.0, 1: 284.0}
RUNOUT = {-1: 386.0, 1: 392.0}
FACE_IDS = (16, 26, 40)  # outer wall, narrow rim, inner wall on source STEP
GAP = 2.1


def read(path):
    return cq.importers.importStep(str(path)).val()


def u_at(y):
    return (y + 445.0) / 890.0


def ease(t):
    t = np.clip(t, 0.0, 1.0)
    return t**3 * (10 + t * (-15 + 6 * t))


def vec(p):
    return np.array(p.Coord())


def intersector(shape):
    r = IntCurvesFace_ShapeIntersector()
    r.Load(shape.wrapped, 1e-7)
    return r


def hits(ray, origin, direction, length=800):
    ray.Perform(gp_Lin(gp_Pnt(*origin), gp_Dir(*direction)), 0, length)
    return [vec(ray.Pnt(i)) for i in range(1, ray.NbPnt() + 1)]


def reface(chin, glass_ray):
    faces = chin.Faces()
    seat = BRep_Tool.Surface_s(faces[FACE_IDS[1]].wrapped)

    # The reconstructed roll has a localized bulge. Route the seat farther
    # underneath it while keeping a continuous, low-curvature painted rail.
    # Elevation stations are independent from the V9 point-by-point trace.
    def corner_fit(sign):
        key, height = {
            -1: (
                [307, 313, 319, 324, 328, 332, 337, 341, 345, 351],
                [
                    213.15,
                    211.26,
                    209.55,
                    208.52,
                    208.62,
                    209.52,
                    211.96,
                    213.63,
                    215.12,
                    217.83,
                ],
            ),
            1: (
                [326, 333, 339, 344, 348, 352, 356, 360, 364, 371],
                [
                    224.70,
                    222.14,
                    220.48,
                    218.91,
                    218.64,
                    219.49,
                    221.26,
                    223.0,
                    224.75,
                    228.1,
                ],
            ),
        }[sign]
        height_line = CubicSpline(key, height, bc_type="natural")
        st = np.arange(STARTS[sign], ENDS[sign] + 5.01, 0.25)
        original = np.array(
            [[vec(seat.Value(u_at(sign * s), v)) for v in (0.0, 1.0)] for s in st]
        )
        target = original.copy()

        def underside(x, s):
            return min(
                q[2] for q in hits(glass_ray, (x, sign * s, 80.0), (0.0, 0.0, 1.0))
            )

        direct_x = []
        front_z = []
        for i, s in enumerate(st):
            y = sign * s
            ridge = max(
                q[0] for q in hits(glass_ray, (100.0, y, 238.6), (-1.0, 0.0, 0.0))
            )
            margin = 3.0 + 5.0 * ease((s - STARTS[sign] - 3.0) / 38.0)
            x = ridge - margin
            blend = ease((s - key[0]) / 9.0)
            z = underside(x, s) - GAP
            if blend:
                z = (1 - blend) * z + blend * height_line(s)
                # At prescribed Z trace the shell's X, rather than pulling
                # the rigid panel up over the sharp local peak.
                iso = max(
                    q[0] for q in hits(glass_ray, (100.0, y, z + GAP), (-1.0, 0.0, 0.0))
                )
                x = (1 - blend) * x + blend * iso
            direct_x.append(x)
            front_z.append(z)
        smooth = lambda a, sigma: gaussian_filter1d(a, sigma / 0.25, mode="nearest")
        blend = ease((st - key[0]) / 7.0)
        x = np.asarray(direct_x) * (1 - blend) + smooth(direct_x, 2.25) * blend
        front_z = np.asarray(front_z) * (1 - blend) + smooth(front_z, 1.3) * blend
        # Fair the fore/aft path while preserving clearance at valley sides.
        # Spread any required clearance correction over several mm of span.
        minimum = np.array(
            [
                max(
                    q[0]
                    for q in hits(
                        glass_ray, (100.0, sign * s, z + 1.25), (-1.0, 0.0, 0.0)
                    )
                )
                if w
                else xx
                for s, xx, z, w in zip(st, x, front_z, blend)
            ]
        )
        corrections = np.maximum(minimum - x, 0.0)
        x += np.max(
            corrections[:, None] * np.exp(-0.5 * ((st[:, None] - st) / 3.0) ** 2),
            axis=0,
        )
        target[:, :, 0] += (x - original[:, 0, 0])[:, None]
        stock = np.array(
            [[underside(q[0], s) for q in row] for s, row in zip(st, target)]
        )
        target[:, 0, 2] = front_z
        back = stock[:, 1] - GAP
        back = np.minimum(
            front_z - 0.15, (1 - blend) * back + blend * smooth(back, 2.25)
        )
        correction = np.maximum(back - stock[:, 1] + 1.0, 0.0)
        target[:, 1, 2] = back - np.max(
            correction[:, None] * np.exp(-0.5 * ((st[:, None] - st) / 3.0) ** 2), axis=0
        )
        # A feathered last 3 mm of span gives a closed, radiused termination
        # at the back of the shared footprint. A small finite installed
        # elastomer section separates the fiberglass and chin at the end.
        endblend = ease((st - (ENDS[sign] - 4.0)) / 4.0)
        target[:, :, 2] = (1 - endblend[:, None]) * target[:, :, 2] + endblend[
            :, None
        ] * (stock - 0.48)
        target = original + ease((st - STARTS[sign]) / 18.0)[:, None, None] * (
            target - original
        )
        return PchipInterpolator(st, target, axis=0)

    fitted_by_side = {sign: corner_fit(sign) for sign in (-1, 1)}

    def offsets(y):
        orig = np.array([vec(seat.Value(u_at(y), v)) for v in (0.0, 1.0)])
        sign = np.sign(y)
        s = abs(y)
        if not sign or s <= STARTS[sign] or s >= RUNOUT[sign]:
            return np.zeros((2, 3))
        fitted = fitted_by_side[sign]
        end = ENDS[sign]
        if s <= end:
            return fitted(s) - orig
        # Carry the tangent around the rear of the contact land before
        # fading into the existing long roll. The two stock lower tangent
        # rails and both wing attachment sections remain exact.
        p0 = fitted(end)
        deriv = (p0 - fitted(end - 0.15)) / 0.15
        d = s - end
        extension = p0 + 4.0 * (1.0 - np.exp(-d / 4.0)) * deriv
        extension[:, 1] = y
        return (extension - orig) * (1.0 - ease(d / (RUNOUT[sign] - end)))

    surfaces = [BRep_Tool.Surface_s(faces[i].wrapped).Copy() for i in FACE_IDS]
    for surface in surfaces:
        for sign in (-1, 1):
            for s in np.arange(STARTS[sign] - 2.0, ENDS[sign] + 4.1, 1.0):
                surface.InsertUKnot(u_at(sign * s), 1, 1e-9, False)
    surface = surfaces[1]
    knots = np.repeat(
        [surface.UKnot(i) for i in range(1, surface.NbUKnots() + 1)],
        [surface.UMultiplicity(i) for i in range(1, surface.NbUKnots() + 1)],
    )
    greville = np.convolve(knots[1:-1], np.ones(3) / 3.0, mode="valid")
    sample = np.array([offsets(890 * u - 445) for u in greville])
    system = BSpline.design_matrix(greville, knots, 3).toarray()
    coefficients = np.linalg.solve(system, sample.reshape(len(sample), 6)).reshape(
        -1, 2, 3
    )
    coefficients[
        (890 * greville - 445 < -RUNOUT[-1]) | (890 * greville - 445 > RUNOUT[1])
    ] = 0.0
    for i, (outside, inside) in enumerate(coefficients, 1):
        for surf, ds in zip(
            surfaces,
            [
                [np.zeros(3), np.zeros(3), outside * 2 / 3, outside],
                np.linspace(outside, inside, 4),
                [inside, inside * 2 / 3, np.zeros(3), np.zeros(3)],
            ],
        ):
            for j, d in enumerate(ds, 1):
                if np.any(d):
                    surf.SetPole(i, j, gp_Pnt(*(vec(surf.Pole(i, j)) + d)))
    sew = BRepBuilderAPI_Sewing(2e-5)
    for i, old in enumerate(faces):
        if i in FACE_IDS:
            surf = surfaces[FACE_IDS.index(i)]
            face = BRepBuilderAPI_MakeFace(
                surf, *BRepTools.UVBounds_s(old.wrapped), 1e-7
            ).Face()
            face.Orientation(old.wrapped.Orientation())
            sew.Add(face)
        else:
            sew.Add(old.wrapped)
    sew.Perform()
    shells = cq.Shape.cast(sew.SewedShape()).Shells()
    assert len(shells) == 1 and shells[0].Closed(), (len(shells), sew.NbFreeEdges())
    part = cq.Solid.makeSolid(shells[0])
    if part.Volume() < 0:
        part = cq.Solid(part.wrapped.Reversed())
    assert part.isValid()
    return part, surfaces[1]


def seal_part(seat, glass):
    low, high = -ENDS[-1], ENDS[1]
    face = BRepBuilderAPI_MakeFace(seat, u_at(low), u_at(high), 0.08, 0.92, 1e-7).Face()
    blank = cq.Shape.cast(BRepPrimAPI_MakePrism(face, gp_Vec(0, 0, 24)).Shape())
    if blank.Volume() < 0:
        blank = cq.Shape.cast(blank.wrapped.Reversed())
    witness = vec(seat.Value(0.5, 0.5)) + [0, 0, 0.35]
    parts = blank.split(glass).Solids()
    (result,) = [s for s in parts if s.isInside(cq.Vector(*witness))]
    assert result.isValid()
    # Subdivide only along the joint; these exact common boundaries improve
    # the default volume integration for the long trimmed glass surface.
    planes = [
        cq.Face.makePlane(1000, 1000, cq.Vector(0, y, 200), cq.Vector(0, 1, 0))
        for y in range(-330, 356, 20)
    ]
    strips = result.split(*planes).Solids()
    return strips[0].fuse(*strips[1:])


def export(part, name):
    path = OUT / (name + ".step")
    cq.exporters.export(part, str(path))
    recovered = read(path)
    assert (
        recovered.isValid()
        and len(recovered.Solids()) == 1
        and recovered.Volume(1e-6) > 0
    )
    recovered.exportStl(str(path.with_suffix(".stl")), 0.04, 0.075, False, False)
    return recovered


def main():
    OUT.mkdir(exist_ok=True)
    chin, glass = read(CHIN), read(GLASS)
    glass_ray = intersector(glass)
    revised, seat = reface(chin, glass_ray)
    print("rigid CAD valid", flush=True)
    revised = export(revised, "chin")
    print("reopened and exported chin", flush=True)
    seal = export(seal_part(seat, glass), "seal")
    print("reopened and exported seal", flush=True)
    verify(seat, revised, seal, glass, glass_ray)


def verify(seat, chin, seal, glass, glass_ray):
    seal_ray = intersector(seal)
    chin_ray = intersector(chin)
    records = []
    for y in np.unique(
        np.r_[
            np.linspace(-ENDS[-1] + 0.07, ENDS[1] - 0.07, 166),
            np.arange(-ENDS[-1] + 0.03, -263.0, 0.65),
            np.arange(284.15, ENDS[1] - 0.01, 0.65),
        ]
    ):
        for v in (0.11, 0.5, 0.89):
            p = vec(seat.Value(u_at(y), v))
            top = min(q[2] for q in hits(glass_ray, (p[0], y, 80), (0, 0, 1)))
            zs = sorted(q[2] for q in hits(seal_ray, p - [0, 0, 0.15], (0, 0, 1), 35))
            czs = hits(chin_ray, p + [0, 0, 0.15], (0, 0, -1), 1.0)
            assert zs and czs, (y, v, p, zs, czs)
            records.append(
                [
                    float(y),
                    v,
                    top - p[2],
                    max(abs(zs[0] - max(q[2] for q in czs)), abs(zs[-1] - top)),
                ]
            )
    rows = np.array(records)
    # Distances / heights are in installed Z. Free gasket thickness and
    # compression percentage require the actual fabricated parts.
    info = {
        "frame": "car XYZ millimetres; X forward, Y left, Z up",
        "source_chin": str(CHIN.relative_to(D)),
        "source_bumper": str(GLASS.relative_to(D)),
        "previous_gasket_limits_y_mm": [-305, 325],
        "contact_limits_y_mm": [-ENDS[-1], ENDS[1]],
        "front_edge_at_gasket_ends_xyz_mm": [
            vec(seat.Value(u_at(y), 0.08)).tolist() for y in (-ENDS[-1], ENDS[1])
        ],
        "wall_runout_ends_y_mm": [-RUNOUT[-1], RUNOUT[1]],
        "sample_count": len(rows),
        "gasket_installed_z_height_range_mm": [rows[:, 2].min(), rows[:, 2].max()],
        "maximum_sampled_chin_and_bumper_contact_error_mm": float(rows[:, 3].max()),
        "chin_volume_mm3": chin.Volume(1e-6),
        "seal_volume_mm3": seal.Volume(1e-6),
        "interferences_mm3": {},
    }
    for name, a, b in [
        ("chin_bumper", chin, glass),
        ("chin_seal", chin, seal),
        ("seal_bumper", seal, glass),
    ]:
        info["interferences_mm3"][name] = sum(
            abs(k.Volume(1e-6)) for k in a.intersect(b).Solids()
        )
        print(name, info["interferences_mm3"][name], flush=True)
    print(info, flush=True)
    assert rows[:, 2].min() > 0 and rows[:, 3].max() < 0.03
    assert max(info["interferences_mm3"].values()) < 0.05
    write_report(info, seat, glass_ray)


def write_report(info, seat, glass_ray):
    paths = [
        CHIN,
        GLASS,
        D / "full_folded_chin/seal_installed_mm.step",
        *(
            OUT / (part + suffix)
            for part in ("chin", "seal")
            for suffix in (".step", ".stl")
        ),
    ]
    info["sha256_by_path_relative_to_deliverables"] = {
        str(path.relative_to(D)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in paths
    }
    info["terminal_measurements"] = []
    for sign in (-1, 1):
        for d in (0.0, 1.0, 2.0, 3.0):
            y = sign * (ENDS[sign] + d)
            depths = []
            for v in (0.08, 0.50, 0.92):
                pt = vec(seat.Value(u_at(y), v))
                depths.append(
                    min(
                        p[2] for p in hits(glass_ray, (pt[0], y, 80.0), (0.0, 0.0, 1.0))
                    )
                    - pt[2]
                )
            info["terminal_measurements"].append(
                {
                    "y_mm": y,
                    "distance_outboard_of_tip_mm": d,
                    "vertical_glass_to_rim_distances_mm": depths,
                }
            )
    info["stl_meshes"] = {}
    for part in ("chin", "seal"):
        mesh = trimesh.load_mesh(OUT / (part + ".stl"))
        assert mesh.is_watertight and mesh.is_winding_consistent
        info["stl_meshes"][part] = {
            "triangle_count": len(mesh.faces),
            "watertight": bool(mesh.is_watertight),
            "consistent_winding": bool(mesh.is_winding_consistent),
        }
    (OUT / "joint_checks.json").write_text(json.dumps(info, indent=2) + "\n")


if __name__ == "__main__":
    main()
