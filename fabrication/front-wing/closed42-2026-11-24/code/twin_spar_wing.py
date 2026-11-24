"""Geometric twin-spar concept. All STEP and STL output stays in car-frame mm."""

import json
from hashlib import sha256
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh
from fold70 import chord
from inboard_mounts_v4 import through_openings
from OCP.BRep import BRep_Tool
from OCP.GeomConvert import GeomConvert_BSplineCurveToBezierCurve
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from scipy.optimize import brentq
from scipy.special import comb
from shapely.geometry import Point, Polygon
from splitter_chin_v1 import swept_solid

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "deliverables"
OUT = D / "twin_spar_wing"
SOURCE_CHIN = D / "fold70/full_folded_chin_mm.step"
SOURCE_PLATES = D / "bracket/outer_plates_v2_car_frame.step"
SOURCE_WEB = D / "bracket/inboard_mounts_v4_mm.step"
SOURCE_GLASS = D / "front_end_v9/fiberglass_v9_mm.step"
PLATE = json.loads((ROOT / "grid/plate_v2.json").read_text())
PLATE_POLYGON = Polygon(PLATE["outer"], PLATE["cutouts"])
SIGNS = {"left": 1, "right": -1}
WHEEL_Y = {"left": 596.0, "right": -585.1}
NOSE_X = {"left": 26.65078, "right": 26.50699}
SPAR_Z = {"left": 115.0, "right": 125.0}
STATIONS = {"fore": -60.0, "aft": -189.0}
LEVEL_BY = {"left": 444.0, "right": 454.0}
CHIN_SEAM = 406.0
TOP_Z = 137.5
TAIL_X = -220.0
FOLD_X = -170.0
RISE = 5.0
FOLD_RADIUS = 18.0
WALL = 3.6
TUBE_RADIUS = 5.0
BORE_RADIUS = 5.25
TUBE_WALL = 1.5
PLATE_TRIM_X = 20.0
PROFILE_GAP = 0.35
MOUNT_BEARING_RADIUS = 6.3
ARC_ANGLE = brentq(
    lambda a: (
        FOLD_RADIUS * (1 - np.cos(a))
        + (FOLD_X - TAIL_X - FOLD_RADIUS * np.sin(a)) * np.tan(a)
        - RISE
    ),
    0.05,
    0.25,
)
RAMP_X = FOLD_X - FOLD_RADIUS * np.sin(ARC_ANGLE)


def vec(point):
    return cq.Vector(*map(float, point))


def read(path):
    return cq.importers.importStep(str(path)).val()


def box(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, vec((x0, y0, z0)))


def side_box(side, x0, x1, y0, y1, z0, z1):
    low, high = sorted((SIGNS[side] * y0, SIGNS[side] * y1))
    return box(x0, x1, low, high, z0, z1)


def tube(x, z, y0, y1, radius=TUBE_RADIUS):
    return cq.Solid.makeCylinder(
        radius, abs(y1 - y0), vec((x, y0, z)), vec((0, np.sign(y1 - y0), 0))
    )


def part_check(part, name):
    assert part.isValid() and len(part.Solids()) == 1 and part.Volume(1e-8) > 0, name
    return part


def plate_frame(side, face=0.0):
    u, v, n = np.array(PLATE["to_car"][side]["R"]).T
    origin = np.array(PLATE["to_car"][side]["t"]) + face * n
    return origin, u, v, n


def plate_y(side, x, z, face=0.0):
    origin, _, _, n = plate_frame(side, face)
    return origin[1] - (n[0] * (x - origin[0]) + n[2] * (z - origin[2])) / n[1]


def plate_halfspace(side, face, outward):
    origin, u, _, n = plate_frame(side, face)
    plane = cq.Plane(origin=tuple(origin), xDir=tuple(u), normal=tuple(n))
    return cq.Workplane(plane).rect(1800, 1000).extrude(900 if outward else -900).val()


def rounded_plan(points, radii, z=50.0, height=220.0):
    corners = []
    for i, (point, radius) in enumerate(zip(points, radii)):
        entry = point - points[i - 1]
        exit = points[(i + 1) % len(points)] - point
        entry, exit = entry / np.linalg.norm(entry), exit / np.linalg.norm(exit)
        turn = np.arctan2(entry[0] * exit[1] - entry[1] * exit[0], entry @ exit)
        setback = radius * np.tan(abs(turn) / 2)
        start, end = point - setback * entry, point + setback * exit
        center = start + radius * np.sign(turn) * np.array([-entry[1], entry[0]])
        tangent_midpoint = (start + end) / 2 - center
        middle = center + radius * tangent_midpoint / np.linalg.norm(tangent_midpoint)
        corners.append([vec((*p, z)) for p in [start, middle, end]])
    edges = []
    for i, (start, middle, end) in enumerate(corners):
        edges += [
            cq.Edge.makeLine(corners[i - 1][-1], start),
            cq.Edge.makeThreePointArc(start, middle, end),
        ]
    return cq.Solid.extrudeLinear(cq.Wire.assembleEdges(edges), [], vec((0, 0, height)))


def section_edges(y, front):
    def point(x, height):
        return vec((x, y, TOP_Z + height))

    def on_arc(angle):
        return point(
            FOLD_X - FOLD_RADIUS * np.sin(angle), FOLD_RADIUS * (1 - np.cos(angle))
        )

    start, crease = point(front, 0.0), point(FOLD_X, 0.0)
    ramp, end = on_arc(ARC_ANGLE), point(TAIL_X, RISE)
    down = vec((0, 0, -WALL))
    top = [
        cq.Edge.makeLine(start, crease),
        cq.Edge.makeThreePointArc(crease, on_arc(ARC_ANGLE / 2), ramp),
        cq.Edge.makeLine(ramp, end),
    ]
    return [
        *top,
        cq.Edge.makeLine(end, end + down),
        *[edge.translate(down).reverse() for edge in reversed(top)],
        cq.Edge.makeLine(start + down, start),
    ]


def skin_blank(side, y0, y1):
    sign = SIGNS[side]
    wire = cq.Wire.assembleEdges(section_edges(sign * y0, NOSE_X[side]))
    return cq.Solid.extrudeLinear(wire, [], vec((0, sign * (y1 - y0), 0)))


def section_controls(y, side):
    curves = []
    for edge in section_edges(y, NOSE_X[side]):
        start, end = (
            np.array(p.toTuple()) for p in (edge.startPoint(), edge.endPoint())
        )
        if edge.geomType() == "LINE":
            curves.append(np.linspace(start, end, 4))
        else:
            tangent = [np.array(edge.tangentAt(t).toTuple()) for t in (0.0, 1.0)]
            handle = 4 * FOLD_RADIUS * np.tan(ARC_ANGLE / 4) / 3
            curves.append(
                [start, start + handle * tangent[0], end - handle * tangent[1], end]
            )
    return np.array(curves)


def wing(side):
    sign = SIGNS[side]
    tip = abs(WHEEL_Y[side])
    nose = NOSE_X[side]
    trim = rounded_plan(
        np.array([(TAIL_X, 440), (nose, 440), (nose, 479), (-22, tip), (TAIL_X, tip)])
        * [1, sign],
        [5, 6, 18, 14, 13],
    )
    result = skin_blank(side, 435, tip + 8).intersect(trim)
    return part_check(
        result.intersect(plate_halfspace(side, PROFILE_GAP, True)).clean(), side
    )


def face_datum_distance(side, x, z):
    """Conservative center-to-stock-edge gap over both faces of the steel."""
    origin, u, v, _ = plate_frame(side)
    distances = []
    for face in (0.0, -PLATE["thickness_mm"]):
        position = np.array((x, plate_y(side, x, z, face), z)) - origin
        point = Point(position @ u, position @ v)
        assert PLATE_POLYGON.contains(point)
        distances += [point.distance(PLATE_POLYGON.boundary)]
        distances += [
            point.distance(Point(hole["uv"])) - hole["dia"] / 2
            for hole in PLATE["holes"].values()
        ]
    return min(distances)


def mount_rail(side):
    """Retain Fold70's original B/E rail footprint, bore datum and relief."""
    origin, u, v, n = plate_frame(side, -PLATE["thickness_mm"])
    plane = cq.Plane(origin=tuple(origin), xDir=tuple(u), normal=tuple(n))
    b, e = [np.array(PLATE["holes"][key]["uv"]) for key in ("B", "E")]
    lo, hi = b[0] - 8.0, e[0] + 8.0
    slope = (e[1] - b[1]) / (e[0] - b[0])

    def lower(a):
        return b[1] + slope * (a - b[0]) - 8.1

    rail = (
        cq.Workplane(plane)
        .polyline([(lo, lower(lo)), (hi, lower(hi)), (hi, 45.0), (lo, 45.0)])
        .close()
        .extrude(-6.0)
        .val()
    )
    exposed_edges = [
        edge
        for edge in rail.Edges()
        if abs(edge.tangentAt().dot(vec(n))) > 0.999 and edge.Center().z < 122.0
    ]
    rail = rail.fillet(6.0, exposed_edges)
    # Both sides of the rail lie within the last horizontal portion of the chin.
    rail = rail.intersect(box(-65, 32, -500, 500, 60, TOP_Z - WALL + 1.0))
    tools = []
    for station in (b, e):
        center = origin + station[0] * u + station[1] * v
        tools.append(cq.Solid.makeCylinder(3.4, 10.0, vec(center + n), vec(-n)))
    return part_check(rail.cut(*tools).clean(), f"mount rail {side}")


def native_controls(source, y):
    slices = []
    for f in source.Faces():
        bb = f.BoundingBox()
        if not (bb.ymin < y < bb.ymax):
            continue
        surf = BRep_Tool.Surface_s(f.wrapped)
        if surf.DynamicType().Name() != "Geom_BSplineSurface":
            continue
        if surf.NbUPoles() != 181 or surf.NbVPoles() != 4:
            continue
        u = (y + 445) / 890
        curve = surf.UIso(u)
        a, b = curve.FirstParameter(), curve.LastParameter()
        p, q = curve.Value(a), curve.Value(b)
        if max(p.X(), q.X()) > chord(y) + 1e-7:
            limit = brentq(
                lambda t, section=curve: section.Value(t).X() - chord(y), a, b
            )
            if p.X() > q.X():
                a = limit
            else:
                b = limit
        seq = GeomConvert_BSplineCurveToBezierCurve(curve, a, b, 1e-12)
        assert seq.NbArcs() == 1, (y, seq.NbArcs())
        bezier = seq.Arc(1)
        assert bezier.NbPoles() == 4
        slices.append(np.array([bezier.Pole(i).Coord() for i in range(1, 5)]))
    assert len(slices) == 7, (y, len(slices))
    first = max(
        slices, key=lambda e: max(e[0, 0], e[-1, 0]) + max(e[0, 2], e[-1, 2]) * 0.05
    )
    remaining = [curve for curve in slices if curve is not first]
    if first[0, 0] < first[-1, 0]:
        first = first[::-1]
    ordered = [first]
    while remaining:
        endpoint = ordered[-1][-1]
        edge = min(
            remaining,
            key=lambda e: min(np.linalg.norm(p - endpoint) for p in e[[0, -1]]),
        )
        remaining = [curve for curve in remaining if curve is not edge]
        if np.linalg.norm(edge[-1] - endpoint) < np.linalg.norm(edge[0] - endpoint):
            edge = edge[::-1]
        assert np.linalg.norm(edge[0] - endpoint) < 1e-5, (y, edge[0], endpoint)
        ordered.append(edge)
    ordered.append(np.linspace(ordered[-1][-1], ordered[0][0], 4))
    return np.array(ordered)


def transition(side, source):
    sign = SIGNS[side]
    start = CHIN_SEAM
    finish = LEVEL_BY[side]
    a, b, c = [
        native_controls(source, sign * station)
        for station in (start - 0.2, start, start + 0.2)
    ]
    derivative = (c - a) / 0.4
    last = section_controls(sign * finish, side)
    # Explicit Hermite poles force an exact native crop station and terminal tangent.
    crank = np.array([b, b + derivative * (finish - start) / 3, last, last])
    crank[:, :, :, 1] = sign * np.linspace(start, finish, 4)[:, None, None]
    ts = np.linspace(0, 1, 7)
    params = np.stack(
        [comb(3, i) * ts**i * (1 - ts) ** (3 - i) for i in range(4)], axis=1
    )
    rows = np.einsum("uv,vepa->uepa", params, crank)
    transition = swept_solid(rows, ts)
    landing = (
        skin_blank(side, finish, 485)
        .intersect(plate_halfspace(side, -PLATE["thickness_mm"], False))
        .clean()
    )
    part = transition.fuse(landing, tol=0.00001).clean()
    return part_check(part, f"transition {side}")


def make_chin(source):
    middle = source.intersect(box(-400, 200, -CHIN_SEAM, CHIN_SEAM, 50, 300)).clean()
    regions = [
        transition(side, source).fuse(mount_rail(side)).clean() for side in SIGNS
    ]
    for side, region in zip(SIGNS, regions):
        part_check(region, f"transition and preserved mount {side}")
    result = middle.fuse(*regions, tol=0.00001).clean()
    return part_check(result, "complete Fold70 center and twin-spar end transitions")


def intersector(part):
    inter = IntCurvesFace_ShapeIntersector()
    inter.Load(part.wrapped, 1e-7)
    return inter


def heights(inter, x, y):
    inter.Perform(gp_Lin(gp_Pnt(x, y, 50), gp_Dir(0, 0, 1)), 0.0, 170.0)
    return sorted({round(inter.Pnt(i).Z(), 8) for i in range(1, inter.NbPnt() + 1)})


def flat_under(x):
    if x >= FOLD_X:
        return TOP_Z - WALL
    if x >= RAMP_X:
        return TOP_Z - WALL + FOLD_RADIUS - np.sqrt(FOLD_RADIUS**2 - (x - FOLD_X) ** 2)
    return TOP_Z - WALL + RISE + (TAIL_X - x) * np.tan(ARC_ANGLE)


def saddle_blank(side, x, z, low, high, rear_x=None):
    """A solid transverse saddle with full-width top seat and lower receiver."""
    sign = SIGNS[side]
    # Make the entire top directly on the wing's actual two-facet section.
    x0 = x - 12.0 if rear_x is None else rear_x
    x1 = x + 12.0
    profile = cq.Wire.makePolygon(
        [
            vec((x0, sign * low, z - 8.5)),
            vec((x1, sign * low, z - 8.5)),
            vec((x1, sign * low, flat_under(x1))),
            vec((x0, sign * low, flat_under(x0))),
        ],
        close=True,
    )
    return cq.Solid.extrudeLinear(profile, [], vec((0, sign * (high - low), 0)))


def contact_area(a, b):
    # A boolean common of boundary faces preserves surface area on pure face contact.
    return sum(
        a_face.intersect(b_face).Area()
        for a_face in a.Faces()
        for b_face in b.Faces()
        if a_face.distance(b_face) < 1.0e-6
    )


def support(side, stock, web, bar, skin, chin):
    sign = SIGNS[side]
    z = SPAR_Z[side]
    final_plate = stock.intersect(box(-450, PLATE_TRIM_X, -700, 700, 40, 400)).clean()
    protection = {}
    face_origin, u, v, n = plate_frame(side)
    for label in ("H", "E", "B"):
        position = face_origin + np.array(PLATE["holes"][label]["uv"]) @ np.array(
            [u, v]
        )
        protected = cq.Solid.makeCylinder(
            MOUNT_BEARING_RADIUS, PLATE["thickness_mm"] + 2, vec(position + n), vec(-n)
        )
        margin = (
            stock.intersect(protected).Volume()
            - final_plate.intersect(protected).Volume()
        )
        assert abs(margin) < 0.001, (side, label, margin)
        protection[label] = {
            "stock_outboard_center_mm": position.tolist(),
            "lost_steel_at_bearing_mm3": margin,
        }
    components = {}
    checks = {"stock_mount_H_E_B": protection, "spar_stations": {}}
    clearing_tools = []
    for station, x in STATIONS.items():
        boundary_in = abs(plate_y(side, x, z, -PLATE["thickness_mm"]))
        boundary_out = abs(plate_y(side, x, z))
        # Use the bracket-adjacent final flat as the root receiver land.
        seat_start = LEVEL_BY[side] + 2
        start = seat_start - 1.0
        end = abs(WHEEL_Y[side]) - 13.0
        solid_envelope = tube(x, z, sign * start, sign * end)
        pipe = solid_envelope.cut(
            tube(x, z, sign * (start - 1), sign * (end + 1), TUBE_RADIUS - TUBE_WALL)
        )
        cutter = tube(
            x, z, sign * (boundary_in - 1), sign * (boundary_out + 1), BORE_RADIUS
        )
        penetration = stock.intersect(cutter)
        expected = np.pi * BORE_RADIUS**2 * PLATE["thickness_mm"] / abs(n[1])
        assert abs(penetration.Volume() / expected - 1.0) < 1e-6, (side, station)
        clearing_tools.append(cutter)
        original_clearances = {
            key: {
                "gap_mm": solid_envelope.distance(value),
                "overlap_mm3": solid_envelope.intersect(value).Volume(),
            }
            for key, value in (("web", web), ("bar", bar), ("chin", chin))
        }
        assert all(
            data["overlap_mm3"] < 0.0001 for data in original_clearances.values()
        ), (side, station, original_clearances)
        outside_start, outside_end = boundary_out + 3.0, end - 2.0
        outer = saddle_blank(side, x, z, outside_start, outside_end)
        outer = outer.cut(
            tube(x, z, sign * (outside_start - 1), sign * (outside_end + 1))
        ).clean()

        # Inner terminal receiver bears on the chin in both stations. The aft
        # one extends aft as a coped cleat onto the original diagonal bar.
        if station == "aft":
            blank = saddle_blank(side, x, z, seat_start, boundary_in + 1.1, rear_x=-213)
            blank = blank.cut(web, bar).clean()
        else:
            blank = saddle_blank(side, x, z, seat_start, boundary_in + 1.1)
        inner = (
            blank.intersect(plate_halfspace(side, -PLATE["thickness_mm"] - 0.35, False))
            .cut(tube(x, z, sign * (start - 1), sign * (boundary_in + 2)))
            .clean()
        )
        if station == "aft":
            # Coped bar can sever a lower offcut on car-right. Keep the
            # connected leg that carries the tube bore and the upper seat.
            witness = vec((x + 9.0, sign * (seat_start + 1.5), z + 6.0))
            (inner,) = [solid for solid in inner.Solids() if solid.isInside(witness)]

        outer, inner = [
            part_check(part, f"{name} {station} {side}")
            for name, part in (("outer saddle", outer), ("inner receiver", inner))
        ]
        assert skin.intersect(outer).Volume() < 0.001
        assert chin.intersect(inner).Volume() < 0.001, (
            side,
            station,
            chin.intersect(inner).Volume(),
        )
        if station == "aft":
            bar_area = contact_area(inner, bar)
            assert bar_area > 10.0, (side, station, bar_area)
            assert inner.intersect(bar).Volume() < 0.001
        else:
            bar_area = 0.0
        assert outer.distance(skin) < 1e-5 and inner.distance(chin) < 0.001
        assert (
            pipe.intersect(outer).Volume() < 0.001
            and pipe.intersect(inner).Volume() < 0.001
        )
        nose_datum = face_datum_distance(side, x, z)
        components[f"spar_{station}_{side}"] = pipe
        components[f"saddle_{station}_{side}"] = outer
        components[f"receiver_{station}_{side}"] = inner
        checks["spar_stations"][station] = {
            "centerline_endpoints_car_xyz_mm": [
                [x, sign * start, z],
                [x, sign * end, z],
            ],
            "centerline_length_mm": end - start,
            "inner_face_center_car_xyz_mm": [x, sign * boundary_in, z],
            "outer_face_center_car_xyz_mm": [x, sign * boundary_out, z],
            "cut_envelope_in_actual_stock_mm3": penetration.Volume(),
            "expected_full_disk_through_steel_mm3": expected,
            "minimum_steel_to_stock_edge_mm": nose_datum - BORE_RADIUS,
            "clearances_to_unmodified_stock_support_and_chin": original_clearances,
            "outer_seat_footprint_fore_aft_and_span_mm": [
                24.0,
                outside_end - outside_start,
            ],
            "outer_seat_surface_contact_mm2": contact_area(outer, skin),
            "inner_receiver_surface_contact_to_chin_mm2": contact_area(inner, chin),
            "inner_receiver_surface_contact_to_diagonal_bar_mm2": bar_area,
            "outer_and_inner_saddle_spar_contact_mm2": [
                contact_area(outer, pipe),
                contact_area(inner, pipe),
            ],
        }
    final_plate = part_check(
        final_plate.cut(*clearing_tools).clean(), f"copied plate {side}"
    )
    for station in STATIONS:
        assert (
            final_plate.intersect(components[f"spar_{station}_{side}"]).Volume()
            < 0.0001
        )
    checks["plate_original_through_openings"] = through_openings(stock)
    checks["plate_proposed_through_openings"] = through_openings(final_plate)
    components[f"plate_{side}"] = final_plate
    return components, checks


def export(name, part):
    part_check(part, name)
    step = OUT / f"{name}.step"
    stl = OUT / f"{name}.stl"
    cq.exporters.export(part, str(step))
    reopened = part_check(read(step), name)
    volume = reopened.Volume(1e-8)
    assert abs(volume / part.Volume(1e-8) - 1.0) < 0.0001, name
    reopened.exportStl(str(stl), tolerance=0.045, angularTolerance=0.10, relative=False)
    mesh = trimesh.load_mesh(stl)
    assert mesh.is_volume and mesh.body_count == 1, (
        name,
        mesh.is_watertight,
        mesh.body_count,
    )
    assert abs(mesh.volume / volume - 1.0) < 0.005, (name, mesh.volume, volume)
    print(
        f"{name} valid single STEP solid and watertight STL; {volume:.1f} mm3",
        flush=True,
    )
    return {
        "step": step.name,
        "stl": stl.name,
        "step_sha256": sha256(step.read_bytes()).hexdigest(),
        "solid_count": 1,
        "watertight_stl": True,
        "step_volume_mm3": volume,
        "stl_volume_mm3": mesh.volume,
        "stl_triangle_count": len(mesh.faces),
        "bounds_mm": mesh.bounds.tolist(),
    }


def main():
    OUT.mkdir(exist_ok=True)
    source = read(SOURCE_CHIN)
    source_plates = read(SOURCE_PLATES).Solids()
    source_web = read(SOURCE_WEB).Solids()
    result = {
        "frame": "car frame millimetres. X forward, Y car-left, Z up.",
        "scope": "Geometric concept. No installed fit, strength, joint, or fabrication validation.",
        "source_models": {
            str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
            for p in (SOURCE_CHIN, SOURCE_PLATES, SOURCE_WEB, SOURCE_GLASS)
        },
        "dimensional_assumptions": {
            "wing_top_main_z_mm": TOP_Z,
            "wing_nominal_vertical_wall_mm": WALL,
            "wing_tail_x_mm": TAIL_X,
            "wing_fold_tangent_x_mm": FOLD_X,
            "wing_rise_mm": RISE,
            "wing_rise_fore_aft_length_mm": FOLD_X - TAIL_X,
            "wing_tangent_section_radius_mm": FOLD_RADIUS,
            "wing_tangent_plan_radii_mm": [5, 6, 18, 14, 13],
            "wing_tail_facet_degrees": np.rad2deg(ARC_ANGLE),
            "wing_tip_measured_inside_tire_y_mm": WHEEL_Y,
            "stock_outer_plate_thickness_mm": PLATE["thickness_mm"],
            "plate_copy_concept_nose_trim_x_mm": PLATE_TRIM_X,
            "outboard_skin_to_plate_gap_mm": PROFILE_GAP,
            "spar_od_mm": TUBE_RADIUS * 2,
            "spar_wall_mm": TUBE_WALL,
            "plate_spar_void_diameter_mm": BORE_RADIUS * 2,
            "center_preserved_within_abs_y_mm": CHIN_SEAM,
            "chin_terminal_section_nominally_level_by_abs_y_mm": LEVEL_BY,
            "fasteners_for_saddles_and_retention": "Undetailed",
        },
        "components": {},
        "sides": {},
    }
    components = {f"wing_{side}": wing(side) for side in SIGNS}
    for name, part in components.items():
        result["components"][name] = export(name, part)
    chin = make_chin(source)
    result["components"]["chin"] = export("chin", chin)
    result["chin_vs_fiberglass_overlap_mm3"] = chin.intersect(
        read(SOURCE_GLASS)
    ).Volume()
    assert result["chin_vs_fiberglass_overlap_mm3"] < 0.001, result[
        "chin_vs_fiberglass_overlap_mm3"
    ]
    center = box(-400, 200, -CHIN_SEAM + 0.01, CHIN_SEAM - 0.01, 50, 300)
    result["preserved_fold70_center_difference_mm3"] = (
        chin.intersect(center).cut(source).Volume()
        + source.intersect(center).cut(chin).Volume()
    )
    assert result["preserved_fold70_center_difference_mm3"] < 0.001
    for side, sign in SIGNS.items():
        stock = next(p for p in source_plates if p.Center().y * sign > 0)
        web, bar = sorted(
            [p for p in source_web if p.Center().y * sign > 0],
            key=lambda p: p.Volume(),
            reverse=True,
        )
        skin = components[f"wing_{side}"]
        added, result["sides"][side] = support(side, stock, web, bar, skin, chin)
        result["sides"][side]["wing_level_check"] = {
            str(y): {
                str(x): heights(intersector(skin), x, sign * y)
                for x in (-215, -195, -160, -60)
            }
            for y in (480.0, 520.0, abs(WHEEL_Y[side]) - 5)
        }
        checks = result["sides"][side]["wing_level_check"]
        for samples in checks.values():
            for x, zs in samples.items():
                assert np.allclose(
                    zs, [flat_under(float(x)), flat_under(float(x)) + WALL], atol=1e-6
                )
        for name, part in added.items():
            result["components"][name] = export(name, part)
    (OUT / "components.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
