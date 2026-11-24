"""Replace four parts in the verified installed assembly; round-trip audit the STEP.

Inputs are already in car-frame millimetres. Run from any directory:
  python code/package_closed42_joint.py CHIN.step SEAL.step
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import cadquery as cq
import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'deliverables'
ORIGINAL = D / 'skin_first_wing/installed_wing_first_mm.step'
OUT = D / 'closed42_joint'
DEST = OUT / 'installed_mm.step'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def signature(shape):
    b = shape.BoundingBox()
    return np.array([b.xmin,b.ymin,b.zmin,b.xmax,b.ymax,b.zmax,
                     shape.Area(),sum(abs(s.Volume()) for s in shape.Solids())])


def leaves(assembly):
    return {n.split('/', 1)[1]: (s, loc, color) for s,n,loc,color in assembly}


def record(entry):
    shape, loc, color = entry
    return {'signature': signature(shape.moved(loc)).tolist(),
            'location': [list(x) for x in loc.toTuple()],
            'color': list(color.toTuple()) if color else None,
            'solids': len(shape.Solids())}


def surface_error(shape_a, shape_b):
    meshes = []
    for shape in (shape_a, shape_b):
        vertices, faces = shape.tessellate(0.04, 0.08)
        meshes.append(trimesh.Trimesh(vertices=[v.toTuple() for v in vertices], faces=faces, process=False))
    errors = []
    for source, target in (meshes, meshes[::-1]):
        points, _ = trimesh.sample.sample_surface(source, 1000, seed=42)
        distances = trimesh.proximity.closest_point(target, points)[1]
        errors.append(float(np.max(distances)))
    return errors


def main():
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    paths = {'wing_left': D/'faired42_wing/wing_left.step',
             'wing_right': D/'faired42_wing/wing_right.step',
             'complete_folded_splitter_chin': Path(sys.argv[1]).resolve(),
             'compressed_underside_seal': Path(sys.argv[2]).resolve()}
    for path in paths.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    source_hashes = {str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p): sha(p)
                     for p in [ORIGINAL, *paths.values()]}
    assembly = cq.Assembly.load(str(ORIGINAL))
    before = leaves(assembly)
    assert len(before) == len(list(assembly)), 'duplicate assembly leaf paths'
    for name, path in paths.items():
        node = assembly.objects[name]
        assert not node.children and name in before
        shape = cq.importers.importStep(str(path)).val()
        assert shape.isValid() and len(shape.Solids()) == 1, (name, 'invalid or not single solid')
        node.obj = shape
    expected = leaves(assembly)
    OUT.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="closed42-package-", dir=OUT)) / "installed_mm.step"
    assembly.export(str(stage))
    reopened = leaves(cq.Assembly.load(str(stage)))
    assert set(expected) == set(reopened), (set(expected)-set(reopened), set(reopened)-set(expected))
    max_sig_diff = 0.0
    max_location_diff = 0.0
    max_color_diff = 0.0
    sampled_surface_errors = {}
    for name in expected:
        old, new = record(expected[name]), record(reopened[name])
        assert old['solids'] == new['solids'], name
        sigdiff = np.abs(np.array(old['signature']) - new['signature'])
        if not np.allclose(old['signature'], new['signature'], rtol=1e-7, atol=0.002):
            assert name == 'compressed_underside_seal', (name, sigdiff)
            assert np.allclose(old['signature'][:6], new['signature'][:6], atol=0.002), (name, sigdiff)
            errors = surface_error(expected[name][0].moved(expected[name][1]), reopened[name][0].moved(reopened[name][1]))
            assert max(errors) < 0.06, (name, errors)
            sampled_surface_errors[name] = errors
        locdiff = np.max(np.abs(np.array(old['location']) - new['location']))
        assert locdiff < 1e-6, (name, locdiff)
        assert (old['color'] is None) == (new['color'] is None), name
        cdiff = max(abs(a-b) for a,b in zip(old['color'],new['color'])) if old['color'] else 0
        assert cdiff < 1e-6, (name, cdiff)
        max_sig_diff = max(max_sig_diff, float(max(sigdiff)))
        max_location_diff = max(max_location_diff, float(locdiff))
        max_color_diff = max(max_color_diff, float(cdiff))
    # Explicitly show all other reference geometry and the original placement/color stayed intact.
    for name in before.keys() - paths.keys():
        assert np.allclose(record(before[name])['signature'], record(reopened[name])['signature'], rtol=1e-7, atol=0.002), name
    for name in paths:
        b, a = record(before[name]), record(reopened[name])
        assert np.allclose(b['location'], a['location'], atol=1e-6), name
        assert np.allclose(b['color'], a['color'], atol=1e-6), name
    assert all(sha(ROOT / k if not Path(k).is_absolute() else Path(k)) == v for k,v in source_hashes.items()), 'source changed during export'
    stage.replace(DEST)
    stage.parent.rmdir()
    report = {'source_sha256': source_hashes, 'output_sha256': sha(DEST),
              'leaf_count': len(reopened), 'replacement_parts': {n: record(reopened[n]) for n in paths},
              'unchanged_reference_leaf_count': len(before)-len(paths),
              'max_roundtrip_absolute_signature_difference': max_sig_diff,
              'max_roundtrip_location_difference': max_location_diff,
              'max_roundtrip_color_difference': max_color_diff,
              'seal_bidirectional_sampled_surface_max_distance_mm': sampled_surface_errors,
              'verification': 'Names, world-space bounding boxes/area/volume, solid count, placements and colors checked after STEP reopen. When seal mass properties are unstable, 1000 sampled points per direction check tessellated surfaces at 0.04 mm tessellation tolerance. Signatures and samples are not exact shape equality proofs; this is an assembly preservation audit, not a fit or fabrication certification.'}
    (OUT/'assembly_release.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)

if __name__ == '__main__':
    main()
