"""Closed-section wing delimited by skin geometry and independently fitted spars."""

import json
from hashlib import sha256

import cadquery as cq
import numpy as np
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt
from shapely.geometry import Point, Polygon

import twin_spar_wing as legacy
from twin_spar_wing import (
    ARC_ANGLE,
    CHIN_SEAM,
    FOLD_RADIUS,
    FOLD_X,
    NOSE_X,
    PLATE,
    PLATE_POLYGON,
    PROFILE_GAP,
    RAMP_X,
    RISE,
    ROOT,
    SIGNS,
    SOURCE_CHIN,
    SOURCE_GLASS,
    SOURCE_PLATES,
    SOURCE_WEB,
    TAIL_X,
    TOP_Z,
    WHEEL_Y,
    D,
    box,
    flat_under,
    heights,
    intersector,
    part_check,
    plate_frame,
    plate_halfspace,
    plate_y,
    read,
    rounded_plan,
    side_box,
    transition,
    vec,
)

OUT = D / "skin_first_wing"
DEPTH = 16.0
LIP_DEPTH = 3.6
TAIL_CORE_X = -185.0
NOSE_CORE_X = -27.0
SHELL_WALL = 2.4
TIP_BLEND_LENGTH = 19.0
TIP_DEPTH_RATIO = 0.63
STATIONS = {"fore": -58.0, "aft": -170.0}
SPAR_WIDTH = 16.0
SPAR_HEIGHT = 6.0
SPAR_Z = TOP_Z - DEPTH / 2
CORNER_R = 0.75
FIT = 0.20
TIP_STOP = 22.0
ROOT_ENGAGEMENT = 30.0
PLATE_TRIM_X = legacy.PLATE_TRIM_X
PLATE_T = PLATE["thickness_mm"]
CORE_INTERVALS = ((-216.0, -181.5), (-158.5, -69.5), (-46.5, 24.0))


def top_z(x):
    return flat_under(x) + legacy.WALL


def wing_profile(y, front, ratio=1.0):
    """Exact retained upper line and aft turn with a tapered lower section."""

    def top(x):
        return vec((x, y, top_z(x)))

    def lower(x, full_z):
        return vec((x, y, top_z(x) - ratio * (top_z(x) - full_z)))

    start = top(front)
    fold = top(FOLD_X)
    half = top(FOLD_X - FOLD_RADIUS * np.sin(ARC_ANGLE / 2))
    ramp = top(RAMP_X)
    end = top(TAIL_X)
    rear_lip = lower(TAIL_X, TOP_Z + RISE - LIP_DEPTH)
    rear_core = lower(TAIL_CORE_X, top_z(TAIL_CORE_X) - DEPTH)
    rear_tangent = lower(-198.0, top_z(-198.0) - DEPTH)
    aft_tangent = lower(-211.0, top_z(-211.0) - LIP_DEPTH)
    core_ramp = lower(RAMP_X, top_z(RAMP_X) - DEPTH)
    core_half = lower(half.x, top_z(half.x) - DEPTH)
    core_fold = lower(FOLD_X, TOP_Z - DEPTH)
    fore_core = lower(NOSE_CORE_X, TOP_Z - DEPTH)
    fore_lip = lower(front, TOP_Z - LIP_DEPTH)
    edges = [
        cq.Edge.makeLine(start, fold),
        cq.Edge.makeThreePointArc(fold, half, ramp),
        cq.Edge.makeLine(ramp, end),
        cq.Edge.makeLine(end, rear_lip),
        cq.Edge.makeBezier([rear_lip, aft_tangent, rear_tangent, rear_core]),
        cq.Edge.makeLine(rear_core, core_ramp),
        cq.Edge.makeThreePointArc(core_ramp, core_half, core_fold),
        cq.Edge.makeLine(core_fold, fore_core),
        cq.Edge.makeBezier(
            [
                fore_core,
                lower(-12.0, TOP_Z - DEPTH),
                lower(11.0, TOP_Z - LIP_DEPTH),
                fore_lip,
            ]
        ),
        cq.Edge.makeLine(fore_lip, start),
    ]
    return cq.Wire.assembleEdges(edges)


def wing_plan(side):
    tip = abs(WHEEL_Y[side])
    nose = NOSE_X[side]
    return rounded_plan(
        np.array([(TAIL_X, 440), (nose, 440), (nose, 479), (-22, tip), (TAIL_X, tip)])
        * [1, SIGNS[side]],
        [5, 6, 18, 14, 13],
    )


def plan_inner(blank):
    lower_face = min(blank.Faces(), key=lambda face: face.Center().z)
    wires = lower_face.outerWire().offset2D(-SHELL_WALL)
    (inner,) = wires
    return cq.Solid.extrudeLinear(inner, [], vec((0, 0, 220)))


def front_x(plan_intersector, y):
    plan_intersector.Perform(gp_Lin(gp_Pnt(-300, y, 150), gp_Dir(1, 0, 0)), 0, 500)
    return max(
        plan_intersector.Pnt(i).X() for i in range(1, plan_intersector.NbPnt() + 1)
    )


def nose_fairing_cut(side, plan):
    """Use the recovered plan outline so tip sweep cannot remove the nose taper."""
    tip = abs(WHEEL_Y[side])
    sign = SIGNS[side]
    trace = intersector(plan)
    sections = []
    stations = [
        435.0,
        454.0,
        467.0,
        476.0,
        484.0,
        498.0,
        *np.linspace(512.0, tip - 12.0, 6),
        tip - 8.0,
        tip - 4.0,
        tip - 1.0,
        tip - 0.2,
        tip + 1.0,
    ]
    for y in stations:
        nose = front_x(trace, sign * np.clip(y, 441.0, tip - 0.2))
        base_z = TOP_Z - DEPTH
        lip_z = TOP_Z - LIP_DEPTH
        lead = vec((nose + 0.30, sign * y, lip_z))
        knee = vec((nose - 34.0, sign * y, base_z - 0.01))
        spread = cq.Edge.makeBezier(
            [
                knee,
                vec((nose - 26.0, sign * y, base_z - 0.01)),
                vec((nose - 7.0, sign * y, lip_z)),
                lead,
            ]
        )
        a = vec((nose + 65.0, sign * y, lip_z))
        b = vec((nose + 65.0, sign * y, base_z - 6.0))
        c = vec((knee.x, sign * y, base_z - 6.0))
        sections.append(
            cq.Wire.assembleEdges(
                [
                    spread,
                    cq.Edge.makeLine(lead, a),
                    cq.Edge.makeLine(a, b),
                    cq.Edge.makeLine(b, c),
                    cq.Edge.makeLine(c, knee),
                ]
            )
        )
    return cq.Solid.makeLoft(sections)


def wing_exterior(side, plan):
    tip = abs(WHEEL_Y[side])
    sign = SIGNS[side]
    front = NOSE_X[side]
    flare = tip - TIP_BLEND_LENGTH
    inner = cq.Solid.extrudeLinear(
        wing_profile(sign * 435.0, front), [], vec((0, sign * (flare - 435.0), 0))
    )
    end = cq.Solid.makeLoft(
        [
            wing_profile(sign * y, front, ratio=ratio)
            for y, ratio in (
                (flare, 1.0),
                (flare + 5.0, 0.98),
                (tip + 0.5, TIP_DEPTH_RATIO),
            )
        ]
    )
    full = inner.fuse(end).clean()
    result = full.intersect(plan).cut(nose_fairing_cut(side, plan))
    result = result.intersect(plate_halfspace(side, PROFILE_GAP, True))
    return part_check(result.clean(), f"{side} wing exterior")


def spar_prism(side, x, start, end, clearance=0.0):
    half_width = SPAR_WIDTH / 2 + clearance
    half_height = SPAR_HEIGHT / 2 + clearance
    prism = side_box(
        side,
        x - half_width,
        x + half_width,
        start,
        end,
        SPAR_Z - half_height,
        SPAR_Z + half_height,
    )
    parallel = [
        edge
        for edge in prism.Edges()
        if abs(edge.tangentAt().dot(vec((0, 1, 0)))) > 0.999
    ]
    return prism.fillet(CORNER_R + clearance, parallel)


def spar_passage_margin(side, x):
    steel = PLATE_POLYGON
    for opening in PLATE["holes"].values():
        steel = steel.difference(
            Point(opening["uv"]).buffer(opening["dia"] / 2, quad_segs=48)
        )
    origin, u, v, _ = plate_frame(side)
    w, h = SPAR_WIDTH / 2 + FIT, SPAR_HEIGHT / 2 + FIT
    margins = []
    for face in (0.0, -PLATE_T):
        footprint = []
        for dx, dz in [(-w, -h), (w, -h), (w, h), (-w, h)]:
            px, pz = x + dx, SPAR_Z + dz
            local = np.array((px, plate_y(side, px, pz, face), pz)) - origin
            footprint.append((local @ u, local @ v))
        rectangle = Polygon(footprint)
        assert steel.contains(rectangle), (side, x, rectangle)
        margins.append(steel.boundary.distance(rectangle))
    return min(margins)


def make_wing(side, plan, exterior, sockets):
    """Produce one printable solid with root-accessible lightweighting and spar pockets."""
    end_y = abs(WHEEL_Y[side]) - TIP_STOP
    body = exterior.cut(*sockets).clean()
    inner_plan = plan_inner(plan)
    cavity_shell = cavity_envelope(side, plan)
    x0, x1 = -207.0, 10.0
    for core_lo, core_hi in CORE_INTERVALS:
        # All cavities open only at the plate-facing root. A 2.4 mm lower and
        # upper laminate is retained even where the external section tapers.
        lo, hi = max(core_lo, x0), min(core_hi, x1)
        core = side_box(
            side,
            lo,
            hi,
            433.0,
            end_y - 1.0,
            TOP_Z - DEPTH + SHELL_WALL,
            TOP_Z - SHELL_WALL,
        )
        if lo < -185:
            core = side_box(side, lo, hi, 433.0, end_y - 1.0, 128.6, 138.1)
        # Intersect a safely trimmed version of the exact section; the core
        # profile closes where the thin ends cease to contain a cavity.
        core = core.intersect(inner_plan).intersect(cavity_shell)
        body = body.cut(core).clean()
    return part_check(body, f"{side} wing with internal channels")


def cavity_envelope(side, plan):
    """Chordwise inset envelope where the closed section has room for a cavity."""
    sign = SIGNS[side]
    y = 434.0 * sign
    source = wing_profile(y, NOSE_X[side])
    part = cq.Solid.extrudeLinear(source, [], vec((0, sign * 170, 0)))
    part = part.cut(nose_fairing_cut(side, plan))
    # Intersect two translated copies of the exterior profile. Their common
    # gives the vertical shell offset and naturally clips the thin lips.
    return part.translate(vec((0, 0, SHELL_WALL))).intersect(
        part.translate(vec((0, 0, -SHELL_WALL)))
    )


def center_chin(source):
    middle = source.intersect(box(-400, 200, -CHIN_SEAM, CHIN_SEAM, 50, 300)).clean()
    chin = middle.fuse(*(transition(side, source) for side in SIGNS), tol=0.00001)
    return part_check(chin.clean(), "Fold70 chin without separable B/E rails")


def receiver(side, station, x, bar, web, chin, slot, start, boundary):
    """Create an inboard spar socket plus the aft attachment to the stock diagonal."""
    sign = SIGNS[side]
    low = start - 3.0
    high = boundary + 1.5
    x0 = x - 11.0 if station == "fore" else -213.0
    x1 = x + 11.0
    y = sign * low
    base_z = TOP_Z - DEPTH
    profile = cq.Wire.makePolygon(
        [
            vec((x0, y, base_z)),
            vec((x1, y, base_z)),
            vec((x1, y, flat_under(x1))),
            *(vec((at, y, flat_under(at))) for at in (FOLD_X, RAMP_X) if x0 < at < x1),
            vec((x0, y, flat_under(x0))),
        ],
        close=True,
    )
    blank = cq.Solid.extrudeLinear(profile, [], vec((0, sign * (high - low), 0)))
    blank = blank.intersect(plate_halfspace(side, -PLATE_T - PROFILE_GAP, False))
    shape = blank.cut(chin, web, bar, slot).clean()
    if station == "aft":
        # The diagonal can sever a small aft offcut. Retain the single
        # connected cleat that contains the new spar socket.
        witness = vec((x + 9.5, sign * (start + 1.0), SPAR_Z))
        (shape,) = [solid for solid in shape.Solids() if solid.isInside(witness)]
    return part_check(shape, f"{side} {station} inboard receiver")


def checked_overlap(part, objects):
    result = {}
    for name, other in objects.items():
        overlap = part.intersect(other).Volume()
        assert overlap < 0.0005, (name, overlap)
        result[name] = {"gap_mm": part.distance(other), "overlap_mm3": overlap}
    return result


def contact_area(part, support):
    """Find shared faces without running distance solves on distant splines."""

    def bounds(shape):
        b = shape.BoundingBox()
        return np.array([b.xmin, b.ymin, b.zmin]), np.array([b.xmax, b.ymax, b.zmax])

    nearby = [(face, *bounds(face)) for face in support.Faces()]
    area = 0.0
    for face in part.Faces():
        lo, hi = bounds(face)
        for other, other_lo, other_hi in nearby:
            limits_overlap = np.all(hi >= other_lo - 1e-6) and np.all(
                other_hi >= lo - 1e-6
            )
            if limits_overlap:
                area += face.intersect(other).Area()
    return area


def plate_bearing_checks(side, stock, plate):
    origin, u, v, n = plate_frame(side)
    bearings = {}
    for name, hole in PLATE["holes"].items():
        p = origin + np.array(hole["uv"]) @ np.array([u, v])
        bearing = cq.Solid.makeCylinder(
            hole["dia"] / 2 + 2.75, PLATE_T + 2, vec(p + n), vec(-n)
        )
        removed = stock.intersect(bearing).Volume() - plate.intersect(bearing).Volume()
        if name in ("B", "E", "H"):
            assert abs(removed) < 0.0005, (side, name, removed)
        bearings[name] = {
            "stock_outboard_center_xyz_mm": p.tolist(),
            "lost_steel_inside_bearing_mm3": removed,
        }
    return bearings


def side_parts(side, stock, web, bar, chin, rail):
    sign = SIGNS[side]
    chin = chin.intersect(side_box(side, -240, 34, 415, 482, 115, 155)).clean()
    plan = wing_plan(side)
    exterior = wing_exterior(side, plan)
    components, passages, sockets = {}, [], []
    checks = {"stations": {}}
    for name, x in STATIONS.items():
        boundary_out = abs(plate_y(side, x, SPAR_Z))
        boundary_in = abs(plate_y(side, x, SPAR_Z, -PLATE_T))
        start = boundary_in - ROOT_ENGAGEMENT
        end = abs(WHEEL_Y[side]) - TIP_STOP
        spar = spar_prism(side, x, start, end)
        passage = spar_prism(side, x, boundary_in - 1, boundary_out + 1, FIT)
        socket = spar_prism(side, x, boundary_out - 1, end + 0.5, FIT)
        passages.append(passage)
        sockets.append(socket)
        inboard_tool = spar_prism(side, x, start - 0.5, boundary_in + 1.0, FIT)
        cleat = receiver(
            side, name, x, bar, web, chin, inboard_tool, start, boundary_in
        )
        components[f"spar_{name}_{side}"] = spar
        components[f"receiver_{name}_{side}"] = cleat
        area = (SPAR_WIDTH + 2 * FIT) * (SPAR_HEIGHT + 2 * FIT)
        area -= (4 - np.pi) * (CORNER_R + FIT) ** 2
        expected = area * PLATE_T / abs(plate_frame(side)[-1][1])
        cut_from_stock = stock.intersect(passage).Volume()
        assert abs(cut_from_stock / expected - 1) < 0.00001, (
            side,
            name,
            cut_from_stock,
            expected,
        )
        margin = spar_passage_margin(side, x)
        assert margin >= 7.0, (side, name, margin)
        buried_volume = spar.intersect(exterior).Volume()
        span_core = spar_prism(side, x, boundary_out + 1.0, end)
        assert (
            abs(span_core.intersect(exterior).Volume() / span_core.Volume() - 1) < 1e-6
        )
        chin_area = contact_area(cleat, chin)
        bar_area = contact_area(cleat, bar) if name == "aft" else 0.0
        assert chin_area > 50 and (name == "fore" or bar_area > 15), (
            side,
            name,
            chin_area,
            bar_area,
        )
        w = SPAR_WIDTH / 2 + FIT
        h = SPAR_HEIGHT / 2 + FIT
        wing_laminate = []
        for px in np.linspace(x - w, x + w, 17):
            under, top = heights(intersector(exterior), px, sign * 520.0)
            wing_laminate.append([top - (SPAR_Z + h), SPAR_Z - h - under])
        roof, floor = np.min(wing_laminate, axis=0)
        assert min(roof, floor) >= SHELL_WALL
        checks["stations"][name] = {
            "spar_axis_endpoints_car_xyz_mm": [
                [x, sign * start, SPAR_Z],
                [x, sign * end, SPAR_Z],
            ],
            "spar_span_mm": end - start,
            "root_engagement_to_inner_plate_center_mm": ROOT_ENGAGEMENT,
            "gap_between_spar_end_and_receiver_socket_end_mm": 0.5,
            "spar_axis_at_plate_faces_car_xyz_mm": [
                [x, sign * y, SPAR_Z] for y in (boundary_in, boundary_out)
            ],
            "plate_opening_in_modelled_stock_volume_mm3": cut_from_stock,
            "full_material_expected_cut_volume_mm3": expected,
            "conservative_minimum_plate_web_mm": margin,
            "spar_volume_enclosed_by_blade_exterior_mm3": buried_volume,
            "conservative_minimum_solid_vertical_cover_above_below_socket_mm": [
                roof,
                floor,
            ],
            "spar_to_original_component_clearances": checked_overlap(
                spar,
                {"chin": chin, "mount_rail": rail, "inboard_web": web, "diagonal": bar},
            ),
            "receiver_to_original_component_clearances": checked_overlap(
                cleat,
                {"chin": chin, "mount_rail": rail, "inboard_web": web, "diagonal": bar},
            ),
            "receiver_to_chin_contact_mm2": chin_area,
            "receiver_to_existing_diagonal_contact_mm2": bar_area,
            "receiver_to_spar_clearance_mm": cleat.distance(spar),
        }
    wing = make_wing(side, plan, exterior, sockets)
    plate = stock.intersect(box(-450, PLATE_TRIM_X, -700, 700, 40, 400))
    plate = part_check(plate.cut(*passages).clean(), f"{side} modified plate")
    checks["protected_stock_bearings"] = plate_bearing_checks(side, stock, plate)
    checks["wing_vs_stock_and_supports"] = checked_overlap(
        wing,
        {
            "plate": plate,
            "chin": chin,
            "mount_rail": rail,
            "inboard_web": web,
            "diagonal": bar,
        },
    )
    for station in STATIONS:
        spar = components[f"spar_{station}_{side}"]
        cleat = components[f"receiver_{station}_{side}"]
        checks["stations"][station]["new_parts_clearances"] = checked_overlap(
            spar, {"wing": wing, "plate": plate, "receiver": cleat}
        )
        slot = sockets[list(STATIONS).index(station)]
        checks["stations"][station]["root_accessible_wing_socket_mm3"] = slot.intersect(
            exterior
        ).Volume()
    checks["outer_depth_samples_z_mm"] = {
        str(y): {
            str(x): heights(intersector(exterior), x, sign * y)
            for x in (-218, -200, -170, -100, -58, -28, 6)
        }
        for y in (
            485,
            520,
            abs(WHEEL_Y[side]) - TIP_BLEND_LENGTH - 1,
            abs(WHEEL_Y[side]) - 5,
        )
    }
    plan_trace = intersector(plan)
    checks["leading_edge_depth_0p3_mm_back_from_plan_edge"] = {}
    for y in (480.0, 500.0, 520.0, 545.0, abs(WHEEL_Y[side]) - 6):
        x = front_x(plan_trace, sign * y) - 0.30
        low, high = heights(intersector(exterior), x, sign * y)
        assert high - low < 4.0, (side, x, y, high - low)
        checks["leading_edge_depth_0p3_mm_back_from_plan_edge"][str(y)] = high - low
    checks["wing_blank_and_finished_solid_volume_mm3"] = [
        exterior.Volume(),
        wing.Volume(),
    ]
    checks["cavity_and_slot_volume_mm3"] = exterior.Volume() - wing.Volume()
    checks["plate_original_through_openings"] = legacy.through_openings(stock)
    checks["plate_proposed_through_openings"] = legacy.through_openings(plate)
    components[f"wing_{side}"] = wing
    components[f"plate_{side}"] = plate
    return components, checks


def main():
    legacy.OUT = OUT
    OUT.mkdir(exist_ok=True)
    source = read(SOURCE_CHIN)
    plates = read(SOURCE_PLATES).Solids()
    supports = read(SOURCE_WEB).Solids()
    chin = center_chin(source)
    prior_chin = read(D / "twin_spar_wing/chin.step")
    result = {
        "frame": "Car-frame millimeters. X forward, Y car-left, Z up.",
        "scope": "Geometric concept without tested installed fit or load capacity.",
        "geometry": {
            "show_surface_z_mm": TOP_Z,
            "maximum_vertical_wing_depth_mm": DEPTH,
            "leading_and_trailing_lip_width_through_section_mm": LIP_DEPTH,
            "cavity_vertical_skin_thickness_mm": SHELL_WALL,
            "aft_profiler_x_and_rise_mm": [FOLD_X, TAIL_X, RISE],
            "starting_planform_retained": True,
            "tip_blend_span_mm": TIP_BLEND_LENGTH,
            "tip_depth_scale_at_loft_terminal": TIP_DEPTH_RATIO,
            "tire_inside_edge_y_mm": WHEEL_Y,
            "spar_cross_section_width_X_and_height_Z_mm": [SPAR_WIDTH, SPAR_HEIGHT],
            "spar_corner_radius_mm": CORNER_R,
            "spar_fit_gap_each_side_mm": FIT,
            "spar_socket_opening_width_X_and_height_Z_mm": [
                SPAR_WIDTH + 2 * FIT,
                SPAR_HEIGHT + 2 * FIT,
            ],
            "stock_steel_thickness_mm": PLATE_T,
            "retained_plate_copy_nose_trim_x_mm": PLATE_TRIM_X,
            "spar_station_selection": (
                "Parallel axes centered vertically in the flat blade core. The earlier aft X=-189 mm "
                "station crosses a factory plate cutout at this height on the left. X=-170 mm uses "
                "the solid web on both sides. Each rear receiving cleat extends to the stock diagonal."
            ),
            "root_to_plate_gap_mm": PROFILE_GAP,
            "root_retention": (
                "Modeled slot fits use 0.20 mm clearance per face. Positive spar retention, receiver "
                "attachment and skin bond material/fasteners, fatigue and strength remain unresolved."
            ),
        },
        "source_models": {
            str(p.relative_to(ROOT)): sha256(p.read_bytes()).hexdigest()
            for p in (SOURCE_CHIN, SOURCE_PLATES, SOURCE_WEB, SOURCE_GLASS)
        },
        "components": {},
        "sides": {},
    }
    rails = {}
    for side in SIGNS:
        rails[side] = part_check(
            legacy.mount_rail(side).cut(chin).clean(), f"{side} B/E rail"
        )
    restored = part_check(
        chin.fuse(*rails.values(), tol=0.00001).clean(), "split chin reassembled"
    )
    delta = restored.Volume(1e-8) - prior_chin.Volume(1e-8)
    assert abs(delta) < 0.001, delta
    old, new = intersector(prior_chin), intersector(restored)
    station_count = 0
    for y in (
        -466,
        -461,
        -453,
        -430,
        -406,
        -315,
        -220,
        0,
        220,
        315,
        406,
        430,
        445,
        452,
        461,
    ):
        for x in (-210, -192, -168, -140, -93, -62, -52, -37, -28, -14, 9, 17, 23):
            before, after = heights(old, x, y), heights(new, x, y)
            if before or after:
                assert len(before) == len(after) and np.allclose(
                    before, after, atol=1e-5
                ), (x, y, before, after)
                station_count += 1
    result["prior_fold70_chin_and_mounts_check"] = {
        "rebuilt_volume_minus_source_volume_mm3": delta,
        "matched_nonempty_vertical_sections": station_count,
    }
    result["components"]["chin"] = legacy.export("chin", chin)
    for side, sign in SIGNS.items():
        rail = rails[side]
        stock = next(plate for plate in plates if plate.Center().y * sign > 0)
        web, bar = sorted(
            [p for p in supports if p.Center().y * sign > 0],
            key=lambda p: p.Volume(),
            reverse=True,
        )
        added, result["sides"][side] = side_parts(side, stock, web, bar, chin, rail)
        added[f"mount_rail_{side}"] = rail
        for name, part in added.items():
            result["components"][name] = legacy.export(name, part)
    (OUT / "components.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
