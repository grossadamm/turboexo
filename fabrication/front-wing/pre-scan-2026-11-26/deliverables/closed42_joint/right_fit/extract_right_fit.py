"""Extract the two rigid full-scale car-right Closed42 fit pieces.

CAD is X forward, Y left, Z up, in millimetres. The output meshes are
centred in XY, and their lowest vertex is at bed Z=0. Move each +128 mm
in X and Y for a separate plate on the 256 mm P1S bed.
"""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import os

import cadquery as cq
import numpy as np
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, box
import trimesh

DEFAULT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_OUT = Path(__file__).resolve().parent
SOURCE_PATHS = {
    'chin': 'deliverables/closed42_joint/chin.step',
    'rail': 'deliverables/skin_first_wing/mount_rail_right.step',
    'wing': 'deliverables/faired42_wing/wing_right.step',
    'plate_datums': 'grid/plate_v2.json',
}
CUT_Y = -290.
BOOL_TOL_MM = .00001
POSE = {
    'inner': ('flat inboard cut', [0, -1, 0], 151),
    'outer': ('flat wheel-side edge', [0, 1, 0], 124),
}
MESH_TOLERANCE = {'inner': (.022, .075), 'outer': (.018, .06)}
BED_EXTENT_MM = 256
EXCLUDED = (0, 0, 18, 28)
RESERVED_XY_MM = 7.


def check_cad(s):
    assert s.isValid() and len(s.Solids()) == 1 and s.Volume() > 0


def hash_file(path):
    return sha256(path.read_bytes()).hexdigest()


def make_bed_mesh(car_mesh, part, out):
    face, upward, deg = POSE[part]
    base = trimesh.geometry.align_vectors(upward, [0, 0, 1])[:3, :3]
    theta = np.radians(deg)
    yaw = np.array([[np.cos(theta), -np.sin(theta), 0],
                    [np.sin(theta), np.cos(theta), 0], [0, 0, 1]])
    r = yaw @ base
    xyz = car_mesh.vertices @ r.T
    shift = np.r_[-(xyz.min(0) + xyz.max(0))[:2] / 2, -xyz[:, 2].min()]
    mesh = car_mesh.copy()
    mesh.vertices = xyz + shift
    hull = mesh.vertices[ConvexHull(mesh.vertices[:, :2]).vertices, :2]
    centre = BED_EXTENT_MM / 2
    footprint = Polygon(hull + centre).buffer(RESERVED_XY_MM)
    assert box(0, 0, BED_EXTENT_MM, BED_EXTENT_MM).contains(footprint)
    assert not footprint.intersects(box(*EXCLUDED))
    target = out / f'{part}_bed.stl'
    temporary = target.with_suffix('.stl.tmp')
    temporary.write_bytes(mesh.export(file_type='stl'))
    reopened = trimesh.load_mesh(temporary, file_type='stl')
    assert reopened.is_volume and reopened.body_count == 1
    assert abs(reopened.volume / car_mesh.volume - 1) < 1.e-6
    assert reopened.bounds[0, 2] == 0
    assert np.allclose(reopened.bounds[:, :2].mean(0), 0, atol=.00002)
    os.replace(temporary, target)
    zmax = reopened.vertices[reopened.faces, 2].max(1)
    down = reopened.face_normals[:, 2]
    near_bed = zmax <= .020
    overhang = (down < -.64) & ~near_bed
    report = {
        'filename': target.name,
        'sha256': hash_file(target),
        'rotation_car_to_bed': r.tolist(),
        'translation_car_to_bed_mm': shift.tolist(),
        'transform_convention': 'column vectors, bed_point = R @ car_point + t',
        'bed_face': face,
        'yaw_deg': deg,
        'extent_mm': reopened.extents.tolist(),
        'bounds_bed_local_mm': reopened.bounds.tolist(),
        'mesh_volume_mm3': reopened.volume,
        'triangles': len(reopened.faces),
        'watertight': bool(reopened.is_watertight),
        'connected_volume_count': reopened.body_count,
        'face_area_within_0_020_mm_of_bed_mm2': reopened.area_faces[near_bed].sum(),
        'projected_downward_area_beyond_bed_mm2': float(reopened.area_faces[overhang] @ -down[overhang]),
        'model_edge_margin_at_plate_centre_mm': centre - reopened.extents[:2].max() / 2,
        'reserved_envelope_to_excluded_corner_mm': footprint.distance(box(*EXCLUDED)),
    }
    return report, reopened, r, shift


def verify_bores(bed, r, t, plate):
    frame = plate['to_car']['right']
    u, v, n = np.array(frame['R']).T
    rail_face = np.array(frame['t']) - plate['thickness_mm'] * n
    records = {}
    for label in ('B', 'E'):
        bu, bv = plate['holes'][label]['uv']
        center = rail_face + bu*u + bv*v
        azims = np.arange(16)*np.pi/8
        pts = np.array([center] + [center+3.35*(np.cos(a)*u+np.sin(a)*v)
                                  for a in azims])
        origins = (pts+n)@r.T+t
        direction = r @ -n
        hits, indices, _ = bed.ray.intersects_location(
            origins, np.tile(direction, (len(origins), 1)), multiple_hits=True)
        distances = (hits - origins[indices]) @ direction
        assert not np.any((distances >= 0) & (distances <= 8))
        records[label] = {
            'center_on_outer_rail_face_car_mm': center.tolist(),
            'nominal_bore_diameter_mm': 6.8,
            'mesh_test_radius_mm': 3.35,
            'ray_count': len(origins),
            'clear_axial_distance_mm_between_1_mm_face_standoffs': 8.,
        }
    return records


def verify_sockets(bed, r, t):
    records = {}
    for label, x in (('fore', -58.), ('aft', -170.)):
        origin = r @ np.array([x, -450., 129.5]) + t
        direction = r @ np.array([0., -1., 0.])
        hits, _, _ = bed.ray.intersects_location(
            [origin], [direction], multiple_hits=True)
        hit_car = (hits-t)@r
        assert len(hits) == 2
        assert abs(hit_car[:, 1].max() + 563.6) < .01
        records[label] = {
            'centerline_car_x_z_mm': [x, 129.5],
            'blind_end_car_y_mm': hit_car[:, 1].max(),
            'test_confirms': 'open centerline from inboard toward the blind end',
        }
    return records


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    parser.add_argument('--out', type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    sources = {k: args.root / v for k, v in SOURCE_PATHS.items()}
    chin, rail, wing = [cq.importers.importStep(str(sources[k])).val()
                       for k in ('chin', 'rail', 'wing')]
    for s in (chin, rail, wing):
        check_cad(s)
    trim_box = cq.Solid.makeBox(1200, 600+CUT_Y, 500, cq.Vector(-600, -600, 0))
    retained = chin.intersect(trim_box).clean()
    check_cad(retained)
    inner = retained.fuse(rail, tol=BOOL_TOL_MM).clean()
    check_cad(inner)
    v_chin, v_rail, v_inner = [s.Volume(1.e-8) for s in (retained, rail, inner)]
    assert abs(v_inner-v_chin-v_rail) < .001
    plate = json.loads(sources['plate_datums'].read_text())
    report = {
        'car_frame': 'millimetres, X forward, Y left, Z up',
        'scale': 1.0,
        'placement_xy_at_plate_center_mm': [128., 128.],
        'bed_bounds_mm': [0, 0, BED_EXTENT_MM, BED_EXTENT_MM],
        'excluded_bed_corner_mm': list(EXCLUDED),
        'xy_buffer_around_full_model_projection_for_fit_check_mm': RESERVED_XY_MM,
        'buffer_note': 'Geometric allowance for brim and supports; not a sliced toolpath check.',
        'cadquery_version': cq.__version__,
        'input_sha256': {SOURCE_PATHS[k]: hash_file(p) for k, p in sources.items()},
        'parts': {},
    }
    with TemporaryDirectory() as tmp:
        for name, solid in (('inner', inner), ('outer', wing)):
            path = Path(tmp) / f'{name}_car.stl'
            tolerance, angular = MESH_TOLERANCE[name]
            solid.exportStl(str(path), tolerance=tolerance, angularTolerance=angular,
                            relative=False)
            car_mesh = trimesh.load_mesh(path)
            assert car_mesh.is_volume and car_mesh.body_count == 1
            part, bed, r, t = make_bed_mesh(car_mesh, name, args.out)
            cad_volume = solid.Volume(1.e-8)
            assert abs(bed.volume/cad_volume - 1.) < .005
            part['cad_volume_mm3'] = cad_volume
            part['linear_mesh_tolerance_mm'] = tolerance
            part['angular_mesh_tolerance_rad'] = angular
            part['bounds_car_mm'] = car_mesh.bounds.tolist()
            if name == 'inner':
                part['cut_plane_y_mm'] = CUT_Y
                part['preserved_side_of_cut'] = 'Y <= cut_plane_y_mm'
                part['joint_seal_end_y_mm'] = -344.
                part['wall_runout_end_y_mm'] = -386.
                part['nominal_fuse'] = {
                    'retained_chin_mm3': v_chin,
                    'rail_mm3': v_rail,
                    'volume_deviation_from_sum_mm3': v_inner-v_chin-v_rail,
                    'fuzzy_tolerance_mm': BOOL_TOL_MM,
                    'note': 'Face union at nominal location. No added bridge, connector, or material.',
                }
                part['mount_bores'] = verify_bores(bed, r, t, plate)
            else:
                part['blind_spar_socket_checks'] = verify_sockets(bed, r, t)
                part['orientation_note'] = ('The wheel-side face sits on the bed. '
                    'Both spar socket openings face up. The complete faired floor and layered blade '
                    'are unchanged; validate any slicer-generated supports separately.')
            report['parts'][name] = part
    (args.out / 'extraction.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
