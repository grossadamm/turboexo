"""Export the splitter mount cross-web, full pierced hanger and diagonal bar per side.

Run with the CadQuery environment. Geometry and photo provenance are in
``grid/inboard_mounts_v4_geometry.json``. Units and placement match the v2
outer-plate car-frame STEP.
"""

import json
from pathlib import Path

import cadquery as cq
import numpy as np
from cooler_supports_v4 import cooler_surround

ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = ROOT / "grid/inboard_mounts_v4_geometry.json"
STEP = ROOT / "deliverables/bracket/inboard_mounts_v4_mm.step"


def vector(point):
    return cq.Vector(*map(float, point))


def extrude(outline, openings, direction):
    face = cq.Face.makeFromWires(outline, openings)
    return cq.Solid.extrudeLinear(face, vector(direction))


def polygon(points):
    return cq.Wire.makePolygon([vector(p) for p in points], close=True)


def round_polygon(points, radius):
    outline = polygon(points)
    return outline.fillet2D(radius, outline.Vertices())


def outer_join(side, outer, amount):
    """Return the actual inner face of the car-frame outboard plate."""
    pose = outer["to_car"][side]
    rotation = np.array(pose["R"])
    u, v, normal = rotation.T
    origin = np.array(pose["t"]) - amount * normal
    return origin, u, v, normal


def trim_at_plane(body, origin, u, v, keep_direction):
    extent = 1000
    corners = [
        (-extent, -extent),
        (extent, -extent),
        (extent, extent),
        (-extent, extent),
    ]
    patch = polygon([origin + a * u + b * v for a, b in corners])
    halfspace = extrude(patch, [], extent * keep_direction)
    return body.intersect(halfspace).clean()


def outer_trim(body, joint):
    """Keep inboard geometry up to the modeled inner face of the outer plate."""
    origin, u, v, normal = joint
    return trim_at_plane(body, origin, u, v, -normal)


def web_with_hanger(spec, side_sign, joint, thickness, radius):
    anchors = np.array(spec["web_plane_anchors_xyz_mm"])
    a, b, c = np.linalg.solve(np.c_[anchors[:, :2], np.ones(3)], anchors[:, 2])
    normal = np.array([-a, -b, 1.0])
    normal /= np.linalg.norm(normal)

    def web_xyz(xy):
        xy = np.asarray(xy) * [1, side_sign]
        return np.c_[xy, xy @ [a, b] + c]

    y_inner = abs(anchors[0, 1])
    front = np.array(spec["front_edge_xy_mm"], dtype=float)
    rear = np.array(spec["rear_edge_xy_mm"], dtype=float)
    for edge in (front, rear):
        edge[0, 1] -= 1.1
        edge[-1, 1] += 3.0
    front_xyz, rear_xyz = web_xyz(front), web_xyz(rear)
    web_edges = [
        cq.Edge.makeSpline([vector(pt) for pt in front_xyz]),
        cq.Edge.makeLine(vector(front_xyz[-1]), vector(rear_xyz[-1])),
        cq.Edge.makeSpline([vector(pt) for pt in rear_xyz[::-1]]),
        cq.Edge.makeLine(vector(rear_xyz[0]), vector(front_xyz[0])),
    ]
    web_outline = cq.Wire.assembleEdges(web_edges)
    cutouts = [
        round_polygon(web_xyz(points), radius) for points in spec["web_cutouts_xy_mm"]
    ]
    web = outer_trim(extrude(web_outline, cutouts, -thickness * normal), joint)

    hanger_y = side_sign * (y_inner + 1.8)
    origin = np.array([0, hanger_y, anchors[0, 2]])
    rise = np.array([0, spec["hanger_outward_face_dY_dZ"], 1.0])
    cross = np.array([1, 0, 0])
    inward = side_sign * np.cross(cross, rise)
    inward /= np.linalg.norm(inward)
    hanger_lower = web_xyz([spec["front_edge_xy_mm"][0], spec["rear_edge_xy_mm"][0]])[
        :, [0, 2]
    ]
    hanger_lower[:, 1] -= thickness * 0.68
    hanger_xz = np.vstack((hanger_lower, spec["hanger_rear_to_top_to_front_xz_mm"]))

    def hanger_xyz(xz):
        return np.array([origin + x * cross + (z - origin[2]) * rise for x, z in xz])

    oval_params = spec["hanger_oval_xz_mm"]
    theta = np.deg2rad(oval_params["angle_deg"])
    ellipse_x = np.cos(theta) * cross + np.sin(theta) * rise / np.linalg.norm(rise)
    oval = cq.Wire.makeEllipse(
        *oval_params["semi_axes"],
        vector(hanger_xyz([oval_params["center"]])[0]),
        vector(inward),
        vector(ellipse_x),
    )
    holes = [
        round_polygon(hanger_xyz(spec[key]), radius)
        for key in ("hanger_lower_opening_xz_mm", "hanger_upper_opening_xz_mm")
    ]
    hanger = extrude(
        round_polygon(hanger_xyz(hanger_xz), 2.0), [*holes, oval], thickness * inward
    )
    return web.fuse(hanger).clean(), (origin, cross, rise, -inward)


def diagonal_bar(spec, joint, hanger_plane, width, thickness, cross_xz):
    x0, z0 = spec["brace_front_inner_xz_mm"]
    x1, z1 = spec["brace_front_outer_xz_mm"]
    origin, _, _, outer_normal = joint
    outer_y = (
        origin[1]
        - (outer_normal[0] * (x1 - origin[0]) + outer_normal[2] * (z1 - origin[2]))
        / outer_normal[1]
    )
    hanger_origin, hanger_fore, hanger_rise, hanger_outward = hanger_plane
    hanger_y = hanger_origin[1] + hanger_rise[1] * (z0 - hanger_origin[2])
    start = np.array([x0, hanger_y, z0])
    end = np.array([x1, outer_y, z1])
    span = end - start
    across = np.array([cross_xz[0], 0, cross_xz[1]], dtype=float)
    across -= span * np.dot(across, span) / np.dot(span, span)
    across *= width / np.linalg.norm(across)
    normal = np.cross(span, across)
    normal *= np.sign(normal[2]) / np.linalg.norm(normal)
    extension = 5 * span / np.linalg.norm(span)
    start -= extension
    end += extension
    outline = polygon([start, end, end + across, start + across])
    brace = outer_trim(extrude(outline, [], -thickness * normal), joint)
    return trim_at_plane(brace, hanger_origin, hanger_fore, hanger_rise, hanger_outward)


def build():
    params = json.loads(PARAMETERS.read_text())
    outer = json.loads((ROOT / params["outer_reference"]).read_text())
    mounts = json.loads((ROOT / params["cooler_support_reference"]).read_text())
    surround, hardware = cooler_surround(
        mounts["hood_off"]["green_surround_model"],
        mounts["point_fits"],
        mounts["gusset_sections"],
    )
    # Model the concealed rear transition at the lower rail from the mating solids.
    # Limit the subtraction to the lower mounting station.
    lower_region = cq.Solid.makeBox(1000, 1500, 380, cq.Vector(-800, -750, 0))
    lower_surround = surround.intersect(lower_region)
    result = {}
    for side_name, sign in (("left", 1), ("right", -1)):
        spec = params[side_name]
        joint = outer_join(side_name, outer, outer["thickness_mm"])
        web, hanger_plane = web_with_hanger(
            spec,
            sign,
            joint,
            params["web_thickness_mm"],
            params["cutout_corner_radius_mm"],
        )
        brace = diagonal_bar(
            spec,
            joint,
            hanger_plane,
            params["brace_width_mm"],
            params["brace_thickness_mm"],
            params["brace_transverse_xz_direction"],
        )
        bolt = hardware[f"Splitter_mount_interface_lower_fastener_car_{side_name}"]
        relieved_web = web.cut(lower_surround, bolt).clean()
        result[side_name] = {
            "cross_web_and_full_hanger": relieved_web,
            "diagonal_bar": brace,
        }
    return result


def check(shape, expected_solids):
    solids = shape.Solids()
    if len(solids) != expected_solids or any(
        not s.isValid() or s.Volume() <= 0 for s in solids
    ):
        raise ValueError(
            f"Expected {expected_solids} valid solids, found {len(solids)}"
        )
    return sum(s.Volume() for s in solids)


def through_openings(solid):
    # Inner face wires each remove one from the boundary's Euler characteristic.
    face_euler_terms = sum(2 - len(face.Wires()) for face in solid.Faces())
    boundary_euler = len(solid.Vertices()) - len(solid.Edges()) + face_euler_terms
    return (2 - boundary_euler) // 2


def main():
    assembly = cq.Assembly(name="splitter_mount_inboard_pair_mm")
    volume = 0
    for side, parts in build().items():
        side_assembly = cq.Assembly(name=f"car_{side}_inboard")
        for name, shape in parts.items():
            expected_openings = 5 if name == "cross_web_and_full_hanger" else 0
            if through_openings(shape) != expected_openings:
                raise ValueError(
                    f"{side} {name} should have {expected_openings} through-openings"
                )
            part_volume = check(shape, 1)
            volume += part_volume
            box = shape.BoundingBox()
            print(
                f"{side} {name}: {part_volume:.1f} mm^3; "
                f"X {box.xmin:.1f}..{box.xmax:.1f}, Y {box.ymin:.1f}..{box.ymax:.1f}, Z {box.zmin:.1f}..{box.zmax:.1f}"
            )
            side_assembly.add(shape, name=name, color=cq.Color(0.48, 0.69, 0.22))
        assembly.add(side_assembly)
    assembly.export(str(STEP))
    imported = cq.importers.importStep(str(STEP)).val()
    imported_volume = check(imported, 4)
    if sorted(through_openings(solid) for solid in imported.Solids()) != [0, 0, 5, 5]:
        raise ValueError("Through-openings changed on STEP round trip")
    if abs(volume - imported_volume) > 0.1:
        raise ValueError(
            f"Volume changed on STEP round trip: {volume:.2f} to {imported_volume:.2f} mm^3"
        )
    print(f"STEP round trip: four valid solids, {imported_volume:.1f} mm^3 total")


if __name__ == "__main__":
    main()
