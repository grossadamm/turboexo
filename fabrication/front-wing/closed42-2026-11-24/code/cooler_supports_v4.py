"""Recover the visible cooler mounting hardware and green rear supports.

Run `--measure` in the photo environment, then `--step` in the CadQuery
environment. The observations and CAD parameters use the established car frame.
"""

import argparse
import json
import os
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OBSERVATIONS = ROOT / "grid/cooler_supports_v4_observations.json"
PARAMETERS = ROOT / "grid/cooler_supports_v4_measurements.json"
STEP = ROOT / "deliverables/body/cooler_supports_v4_mm.step"
SIZE = np.array([1200, 900])


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


class RegisteredVideo:
    def __init__(self):
        import frame

        self.frame = frame.build()
        self.scale = frame.S
        self.rotation = self.frame["R"]
        self.views = {
            int(name[-9:-4]): view
            for name, view in self.frame["V"].items()
            if name.startswith("video/")
        }

    def ray(self, image, uv):
        view = self.views[int(image)]
        camera = self.frame["to_car"](view.C)[0]
        direction = view.rays(np.array(uv) * [view.w, view.h] / SIZE)[0]
        return camera, direction @ self.rotation.T

    def project(self, image, xyz):
        view = self.views[int(image)]
        world = np.array(xyz) / self.scale @ self.rotation + self.frame["o"]
        return view.project(world)[0] * SIZE / [view.w, view.h]

    def fit_point(self, observations):
        from scipy.optimize import least_squares

        normal_matrix = np.zeros((3, 3))
        normal_rhs = np.zeros(3)
        for image, uv in observations.items():
            origin, ray = self.ray(image, uv)
            p = np.eye(3) - np.outer(ray, ray)
            normal_matrix += p
            normal_rhs += p @ origin
        initial = np.linalg.solve(normal_matrix, normal_rhs)

        def residual(xyz):
            return np.concatenate(
                [self.project(image, xyz)[0] - uv for image, uv in observations.items()]
            )

        return least_squares(residual, initial, loss="soft_l1", f_scale=2).x

    def at_station(self, image, uv, y):
        origin, direction = self.ray(image, uv)
        return origin + (y - origin[1]) / direction[1] * direction


def image_errors(video, position, observations):
    return {
        image: round(float(np.linalg.norm(video.project(image, position)[0] - uv)), 2)
        for image, uv in observations.items()
    }


class HoodOffPhoto:
    def __init__(self, path):
        self.file = path
        pose = json.loads(path.read_text())
        self.rotation = np.array(pose["R"])
        self.translation = np.array(pose["t"])
        self.intrinsics = np.array(pose["K"])
        self.distortion = np.array(pose["distortion"])
        self.origin = -self.rotation.T @ self.translation

    def at_z(self, uv, height):
        import cv2

        xy = cv2.undistortPoints(
            np.array([[uv]], dtype=float), self.intrinsics, self.distortion
        )[0, 0]
        ray = self.rotation.T @ np.r_[xy, 1]
        return self.origin + ray * ((height - self.origin[2]) / ray[2])

    def project(self, points):
        import cv2

        camera_rotation = cv2.Rodrigues(self.rotation)[0]
        return cv2.projectPoints(
            np.array(points, dtype=float),
            camera_rotation,
            self.translation,
            self.intrinsics,
            self.distortion,
        )[0][:, 0]


def hood_off_dimensions(source, fits):
    observation = source["hood_off_picks"]
    photo = HoodOffPhoto(ROOT / observation["registered_pose"])
    alternate = HoodOffPhoto(ROOT / "grid/october_full_car_pose_v4.json")
    upper = fits["upper"]
    links = {}
    for side, picks in observation["links"].items():
        front = np.array(
            [
                upper[f"{side}_ear_{key}_tip"]["xyz_mm"]
                for key in ("inboard", "outboard")
            ]
        )
        front_center = front.mean(axis=0)
        rear_z = picks["modeled_rear_top_z_mm"]
        pixels = picks["rear_tip_pixels"]
        rear_rows = {
            p.file.name: np.array([p.at_z(uv, rear_z) for uv in pixels])
            for p in (photo, alternate)
        }
        rear_x = np.mean([row[:, 0].mean() for row in rear_rows.values()])
        # Constrain the rectangular link to the triangulated leading centers.
        rear_center = np.array([rear_x, front_center[1], rear_z])
        front_bolt = photo.at_z(picks["forward_bolt_pixels"], front_center[2])
        rear_bolt = photo.at_z(picks["rear_bolt_pixels"], rear_z)
        links[side] = {
            "front_tips_xyz_mm": front.round(3).tolist(),
            "rear_center_xyz_mm": rear_center.round(3).tolist(),
            "rear_corners_by_pose_xyz_mm": {
                key: row.round(3).tolist() for key, row in rear_rows.items()
            },
            "rear_x_shift_per_3_mm_height_change_mm": round(
                max(
                    abs(photo.at_z(uv, rear_z + 3)[0] - photo.at_z(uv, rear_z)[0])
                    for uv in pixels
                ),
                3,
            ),
            "front_screw_centre_back_from_leading_edge_mm": round(
                float(np.clip(front_center[0] - front_bolt[0], 13, 27)), 3
            ),
            "rear_screw_centre_forward_of_trailing_edge_mm": round(
                float(np.clip(rear_bolt[0] - rear_x, 9, 17)), 3
            ),
            "width_mm": round(float(np.linalg.norm(front[1] - front[0])), 3),
            "length_x_mm": round(float(front_center[0] - rear_x), 3),
        }
    edge_points = {
        "upper_top_front": 514.0,
        "upper_bottom_front": 491.0,
        "upper_top_rear": 514.0,
        "lower_top_front": 357.0,
        "lower_bottom_front": 335.0,
        "lower_top_rear": 357.0,
        "outboard_post_bottom_front": 333.0,
    }
    frame_rays = {}
    for feature, height in edge_points.items():
        pixels = observation["green_frame_outline"][feature]
        frame_rays[feature] = {
            "height_mm": height,
            "intersections_by_pose_mm": {
                p.file.name: np.array([p.at_z(uv, height) for uv in pixels])
                .round(3)
                .tolist()
                for p in (photo, alternate)
            },
        }
    return {
        "links": links,
        "photo_ray_intersections": frame_rays,
        "green_surround_model": {
            "upper_front_x_at_right_left_mm": [-284, -277],
            "upper_rear_x_at_right_left_mm": [-309, -310],
            "upper_top_z_at_right_left_mm": [515.0, 512.0],
            "upper_bottom_z_at_right_left_mm": [491.0, 488.0],
            "lower_front_x_at_right_left_mm": [-272, -280],
            "lower_rear_x_at_right_left_mm": [-305, -308],
            "lower_top_z_at_right_left_mm": [356.5, 357.0],
            "lower_bottom_z_at_right_left_mm": [335.5, 335.0],
            "outboard_post_y_extents_mm": [-369, 373],
            "post_width_y_mm": 31,
            "post_projected_top_z_at_right_left_mm": [541, 539],
        },
    }


def measure():
    source = json.loads(OBSERVATIONS.read_text())
    video = RegisteredVideo()
    results = {}
    for group, points in source["picked_pixels"].items():
        results[group] = {}
        for name, observations in points.items():
            position = video.fit_point(observations)
            omit = {
                image: round(
                    float(
                        np.linalg.norm(
                            video.fit_point(
                                {k: uv for k, uv in observations.items() if k != image}
                            )
                            - position
                        )
                    ),
                    2,
                )
                for image in observations
            }
            holdouts = source["verification_holdouts"].get(group, {}).get(name, {})
            results[group][name] = {
                "xyz_mm": position.round(3).tolist(),
                "fit_errors_1200x900_px": image_errors(video, position, observations),
                "heldout_errors_1200x900_px": image_errors(video, position, holdouts),
                "leave_one_view_out_shift_mm": omit,
            }
    sections = {}
    for side, record in source["gusset_section_pixels"].items():
        y = record["plane_y_mm"]
        station_samples = {
            image: [
                video.at_station(image, uv, y)[[0, 2]].round(3).tolist() if uv else None
                for uv in section
            ]
            for image, section in record["sections"].items()
        }
        median = np.nanmedian(
            np.array(
                [
                    [xy if xy else [np.nan, np.nan] for xy in values]
                    for values in station_samples.values()
                ]
            ),
            axis=0,
        )
        sections[side] = {
            "plane_y_mm": y,
            "station_order": [
                "leading top",
                "leading knee",
                "visible toe",
                "opening apex",
                "opening forward foot",
                "opening aft foot",
            ],
            "samples_xz_mm": station_samples,
            "median_xz_mm": median.round(3).tolist(),
        }
    write_json(
        PARAMETERS,
        {
            "source": str(OBSERVATIONS.relative_to(ROOT)),
            "frame_mm": source["units"],
            "point_fits": results,
            "gusset_sections": sections,
            "hood_off": hood_off_dimensions(source, results),
        },
    )
    print(PARAMETERS)


def polygon_prism(points, direction, holes=()):
    import cadquery as cq

    def wire(vertices):
        return cq.Wire.makePolygon([cq.Vector(*v) for v in vertices], close=True)

    face = cq.Face.makeFromWires(wire(points), [wire(hole) for hole in holes])
    return cq.Solid.extrudeLinear(face, cq.Vector(*direction))


def bolt(base, height, washer_diameter=16, *, axis=(0, 0, 1), shank_length=0):
    import cadquery as cq

    # Represent the observed washer and hex silhouette without inferring the thread.
    plane = cq.Plane(origin=cq.Vector(*base), normal=cq.Vector(*axis), xDir=(1, 0, 0))
    ring = cq.Workplane(plane).circle(washer_diameter / 2).extrude(2).val()
    head = cq.Workplane(plane).workplane(offset=1.7).polygon(6, washer_diameter * 0.76)
    body = ring.fuse(head.extrude(height - 1.7).val())
    if shank_length:
        shank = cq.Workplane(plane).workplane(offset=0.1).circle(3.6)
        body = body.fuse(shank.extrude(-shank_length).val())
    return body.clean()


def cooler_surround(mesh_parameters, points, sections):
    import cadquery as cq

    p = mesh_parameters
    limits = p["outboard_post_y_extents_mm"]
    y_reach = np.array(limits) - np.sign(limits) * (p["post_width_y_mm"] / 2)

    def tube_ring(group, side, y):
        fore = p[f"{group}_front_x_at_right_left_mm"][side]
        aft = p[f"{group}_rear_x_at_right_left_mm"][side]
        top = p[f"{group}_top_z_at_right_left_mm"][side]
        sole = p[f"{group}_bottom_z_at_right_left_mm"][side]
        return cq.Wire.makePolygon(
            [
                cq.Vector(x, y, z)
                for x, z in [(fore, sole), (fore, top), (aft, top), (aft, sole)]
            ],
            close=True,
        )

    beams = {
        group: cq.Solid.makeLoft(
            [tube_ring(group, ix, y) for ix, y in enumerate(y_reach)], ruled=True
        )
        for group in ("upper", "lower")
    }
    hardware = {}
    for ix, side in enumerate(("car_right", "car_left")):
        mark = p["post_projected_top_z_at_right_left_mm"][ix]
        top_x = p["upper_front_x_at_right_left_mm"][ix]
        base_x = p["lower_front_x_at_right_left_mm"][ix]
        top_aft = p["upper_rear_x_at_right_left_mm"][ix] - 3
        base_aft = p["lower_rear_x_at_right_left_mm"][ix] - 2
        base_z = p["lower_bottom_z_at_right_left_mm"][ix]
        left_plane = min(
            limits[ix], limits[ix] - np.sign(limits[ix]) * p["post_width_y_mm"]
        )
        post_xz = [
            (base_x, base_z),
            (base_x + 1, base_z + 14),
            (top_x, mark - 11),
            (top_x - 5, mark),
            (top_aft + 6, mark),
            (top_aft, mark - 11),
            (base_aft, base_z + 12),
            (base_aft + 3, base_z),
        ]
        beams[side] = polygon_prism(
            [(x, left_plane, z) for x, z in post_xz], [0, p["post_width_y_mm"], 0]
        )
        anchors = points[side]
        seat = np.array(anchors["lower_fastener_seat"]["xyz_mm"])
        crown = np.array(anchors["lower_fastener_crown"]["xyz_mm"])
        top_seat = np.array(anchors["front_gusset_upper_seat"]["xyz_mm"])
        upper_bolt = np.array(
            [top_seat[0] - 16, sections[side]["plane_y_mm"], 506.0 - ix]
        )
        lower_bolt = np.r_[(seat[:2] + crown[:2]) / 2, seat[2]]
        for name, axis, far_x, height, thickness in (
            ("upper", upper_bolt, top_x - 8, 8.5, 8),
            (
                "lower",
                lower_bolt,
                base_x - 8,
                float(np.clip(crown[2] - seat[2], 7, 12)),
                7,
            ),
        ):
            x, y, z = axis
            lug = [
                (far_x, y - 20, z),
                (x - 3, y - 13, z),
                (x + 11, y - 7, z),
                (x + 12, y + 6, z),
                (x - 3, y + 13, z),
                (far_x, y + 20, z),
            ]
            lug_shape = polygon_prism(lug, [0, 0, -thickness])
            shank_length = 0
            if name == "upper":
                # The small green barrel visible between the tabs fills the
                # upper lug-to-hanger spacing. Its exact section is nominal.
                hanger_z = (484.9, 488.9)[ix]
                underside = z - thickness
                barrel = cq.Solid.makeCylinder(
                    6.75, underside - hanger_z, cq.Vector(x, y, hanger_z)
                )
                flange = cq.Solid.makeCylinder(8.5, 2.0, cq.Vector(x, y, hanger_z))
                bore = cq.Solid.makeCylinder(
                    4.3, z - hanger_z + 0.4, cq.Vector(x, y, hanger_z - 0.2)
                )
                hardware[f"Splitter_mount_interface_upper_spacer_{side}"] = (
                    barrel.fuse(flange).cut(bore).clean()
                )
                lug_shape = lug_shape.cut(bore).clean()
                shank_length = z - hanger_z
            beams[f"{name}_{side}_lug"] = lug_shape
            hardware[f"Splitter_mount_interface_{name}_fastener_{side}"] = bolt(
                axis, height, 17, shank_length=shank_length
            )
    frame_solid = (
        beams["upper"]
        .fuse(*(shape for name, shape in beams.items() if name != "upper"))
        .clean()
    )
    return frame_solid, hardware


def upper_link(record, core, surround):
    import cadquery as cq

    front_a, front_b = sorted(
        np.array(record["front_tips_xyz_mm"]), key=lambda point: point[1]
    )
    center = (front_a + front_b) / 2
    lateral = (front_b - front_a) / record["width_mm"]
    reach = np.array(record["rear_center_xyz_mm"]) - center
    depth = np.linalg.norm(reach)
    aft = reach / depth
    normal = np.cross(lateral, aft)
    normal /= np.linalg.norm(normal)
    half_width = record["width_mm"] / 2
    thickness = 3
    profile = [
        (0, -half_width + 2),
        (2, -half_width),
        (depth - 2, -half_width),
        (depth, -half_width + 2),
        (depth, half_width - 2),
        (depth - 2, half_width),
        (2, half_width),
        (0, half_width - 2),
    ]
    link = polygon_prism(
        [center + x * aft + y * lateral for x, y in profile], -thickness * normal
    )
    front = center + record["front_screw_centre_back_from_leading_edge_mm"] * aft
    rear = (
        center + (depth - record["rear_screw_centre_forward_of_trailing_edge_mm"]) * aft
    )
    for anchor in (front, rear):
        drill = cq.Solid.makeCylinder(
            4.2, 8, cq.Vector(*(anchor - 5 * normal)), cq.Vector(*normal)
        )
        link = link.cut(drill)
    # Extend the measured pedestal to the modeled top rail, then trim the mating surface.
    pedestal_top = front - thickness * normal
    pedestal = cq.Solid.makeCylinder(
        7.7, 27, cq.Vector(*pedestal_top), cq.Vector(*(-normal))
    )
    pedestal = pedestal.cut(core).clean()
    core_drill = cq.Solid.makeCylinder(
        4.0, 10, cq.Vector(*(pedestal_top + normal)), cq.Vector(*(-normal))
    )
    pedestal = pedestal.cut(core_drill).clean()
    front_head = bolt(front, 5.5, 12, axis=normal, shank_length=11)
    rear_head = bolt(rear, 5.5, 12, axis=normal, shank_length=11)
    frame_drill = cq.Solid.makeCylinder(
        4.1, 13, cq.Vector(*(rear + normal)), cq.Vector(*(-normal))
    )
    return {
        "upper_link": link.cut(surround).clean(),
        "core_pedestal": pedestal,
        "forward_link_bolt": front_head,
        "rear_link_bolt": rear_head,
    }, frame_drill


def center_tab(eye):
    import cadquery as cq

    # Low video sees the head almost edge-on from the high views.
    tilt = np.deg2rad(15)
    normal = np.array([np.sin(tilt), 0, -np.cos(tilt)])
    across = np.array([0, 1, 0])
    fore = np.cross(across, normal)
    profile = [
        (-8, -10),
        (-5, -12),
        (8, -12),
        (10, -10),
        (10, 10),
        (8, 12),
        (-5, 12),
        (-8, 10),
    ]
    base = eye - 1.5 * normal
    flange = polygon_prism(
        [base + s * fore + t * across for s, t in profile], -3 * normal
    )
    rear = base + 8 * fore
    upturned = polygon_prism(
        [
            rear + [-2, -12, 0],
            rear + [1, -12, 0],
            rear + [1, -12, 15],
            rear + [-3, -12, 13],
        ],
        [0, 24, 0],
    )
    bore = cq.Solid.makeCylinder(
        3.5, 9, cq.Vector(*(eye - 6 * normal)), cq.Vector(*normal)
    )
    clip = flange.fuse(upturned).cut(bore).clean()
    washer = cq.Solid.makeCylinder(
        7, 1.7, cq.Vector(*(eye - 1.65 * normal)), cq.Vector(*normal)
    )
    washer = washer.cut(bore).clean()
    return clip.cut(washer).clean(), washer


def build_components(parameters=PARAMETERS):
    """Return named (shape, color) pairs for a parent car-frame assembly."""
    import cadquery as cq

    data = json.loads(Path(parameters).read_text())
    green = cq.Color(0.52, 0.69, 0.18)
    hardware_green = cq.Color(0.64, 0.75, 0.32)
    alloy = cq.Color(0.75, 0.78, 0.80)
    black = cq.Color(0.15, 0.16, 0.17)
    from intercooler_v4_step import build_parts

    components = {}
    green_parameters = data["hood_off"]["green_surround_model"]
    surround, hardware = cooler_surround(
        green_parameters, data["point_fits"], data["gusset_sections"]
    )
    components["Green_rectangular_cooler_surround_and_mounting_lugs"] = surround, green
    components.update(
        {name: (shape, hardware_green) for name, shape in hardware.items()}
    )
    upper = data["point_fits"]["upper"]
    eye = np.array(upper["center_black_fastener_eye"]["xyz_mm"])
    clip, insert = center_tab(eye)
    components["Center_wired_accessory_above_core"] = clip, black
    components["Center_wired_accessory_eye_insert"] = insert, alloy
    cooler_data = json.loads(
        (ROOT / "grid/intercooler_v4_measurements.json").read_text()
    )
    core = build_parts(cooler_data)[0][1]
    for side, record in data["hood_off"]["links"].items():
        parts, drill = upper_link(record, core, surround)
        surround = surround.cut(drill).clean()
        for label, part in parts.items():
            components[f"Intercooler_{label}_car_{side}"] = (
                part,
                black if label.endswith("bolt") else alloy,
            )
    components["Green_rectangular_cooler_surround_and_mounting_lugs"] = surround, green
    return components


def export_step():
    import cadquery as cq

    assembly = cq.Assembly(name="Visible_intercooler_mounts_and_rear_green_supports_v4")
    components = build_components()
    parts = {}
    for name, (shape, color) in components.items():
        assert shape.isValid() and len(shape.Solids()) == 1 and shape.Volume() > 0, name
        bb = shape.BoundingBox()
        parts[name] = {
            "volume_mm3": round(shape.Volume(), 3),
            "bounding_box_mm": np.round(
                [[bb.xmin, bb.ymin, bb.zmin], [bb.xmax, bb.ymax, bb.zmax]], 3
            ).tolist(),
        }
        assembly.add(shape, name=name, color=color)
    assembly.export(str(STEP))
    restored = cq.importers.importStep(str(STEP)).val()
    assert restored.isValid() and len(restored.Solids()) == len(components)
    reopened = list(restored.Solids())
    volume = sum(shape.Volume() for shape in reopened)
    for name, (shape, _) in components.items():
        match = min(reopened, key=lambda part: part.Center().sub(shape.Center()).Length)
        assert abs(shape.Volume() - match.Volume()) < 0.02, name
        assert match.Center().sub(shape.Center()).Length < 0.01, name
        reopened.remove(match)
    write_json(
        PARAMETERS.with_name("cooler_supports_v4_step_checks.json"),
        {
            "step": str(STEP.relative_to(ROOT)),
            "valid_after_reimport": restored.isValid(),
            "individually_named_solids": len(restored.Solids()),
            "sum_of_component_volumes_mm3": round(volume, 3),
            "components": parts,
        },
    )
    print(f"{STEP}: {len(components)} valid solids")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--measure", action="store_true")
    operation.add_argument("--step", action="store_true")
    args = parser.parse_args()
    os.chdir(ROOT)
    if args.measure:
        measure()
    else:
        export_step()
