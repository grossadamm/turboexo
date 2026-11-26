"""Cross-check mask geometry against the released combined STL."""
from hashlib import sha256
from pathlib import Path
from time import perf_counter
import json

import numpy as np
from geometry import build_masks, mesh_triangles, _write

HERE = Path(__file__).resolve().parent


def stl_triangles(path):
    typ = np.dtype([("normal","<f4",(3,)),("verts","<f4",(3,3)),("attr","<u2")])
    count = np.fromfile(path, dtype="<u4", count=1, offset=80)[0]
    assert 84+count*typ.itemsize == path.stat().st_size
    return np.fromfile(path, dtype=typ, count=count, offset=84)["verts"].astype(float)*[-1,-1,1]


def surface_distances(triangles, probes):
    import vtk
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    points = vtk.vtkPoints()
    points.SetData(numpy_to_vtk(np.ascontiguousarray(triangles.reshape(-1,3)),deep=True))
    cells = vtk.vtkCellArray()
    cells.SetData(numpy_to_vtkIdTypeArray(np.arange(0,3*(len(triangles)+1),3,dtype="int64"),deep=True),
                  numpy_to_vtkIdTypeArray(np.arange(3*len(triangles),dtype="int64"),deep=True))
    surf = vtk.vtkPolyData()
    surf.SetPoints(points)
    surf.SetPolys(cells)
    assert surf.GetNumberOfCells() == len(triangles)
    locator = vtk.vtkStaticCellLocator()
    locator.SetDataSet(surf)
    locator.BuildLocator()
    cell, sub, d2, close = vtk.reference(0), vtk.reference(0), vtk.reference(0.), [0.,0.,0.]
    for p in probes:
        locator.FindClosestPoint(p,close,cell,sub,d2)
        yield float(d2.get())**.5


def main():
    p = HERE.parent / "faired42_wing/wing_right.stl"
    accepted = stl_triangles(p)
    x,y,z = axes = tuple(np.arange(a,b,1.)+.37 for a,b in [(-28,222),(468,587),(119,214)])
    mask_sources = [np.zeros(tuple(map(len,axes)),bool) for _ in range(2)]
    _write(mask_sources[0],axes,accepted,2)
    for name in ("wing_control","upper_blade"):
        _write(mask_sources[1],axes,mesh_triangles(name),2)
    union = mask_sources[0]|mask_sources[1]
    diff = mask_sources[0]^mask_sources[1]
    native = {"cad_1mm_center_sample_raw_solid_voxels": int(union.sum()),
        "recombined_vs_released_stl_mismatch_voxels": int(diff.sum()),
        "overlap_fraction_of_union": float(1-diff.sum()/union.sum()),
        "accepted_stl_sha256": sha256(p.read_bytes()).hexdigest(),
        "description": "Native solids (no sheet snapping, no wing cavity fill) on the same 1 mm sample lattice. Small changes near surface can arise from different approved STL and standalone blade tessellation."}
    assert native["overlap_fraction_of_union"] > .998, native
    try:
        probes = np.array([a[i] for a,i in zip(axes,np.where(diff))]).T
        dist = np.array(list(surface_distances(accepted, probes)))
        native["mismatch_distance_to_accepted_stl_surface_p50_p95_max_mm"] = np.quantile(dist,[.5,.95,1]).tolist()
        assert dist.max() < .3
    except ImportError:
        pass

    results=[]
    for h in (3.5, 2.3, 1.5):
        def centers(a,b,c,d,step):
            return np.sort(np.r_[np.arange(a,b,20.), np.arange(b,c,step) + step/2, np.arange(c,d,20.)])
        axes = [centers(-1500,110,250,2250,h*1.5),
                centers(10,500,600,2200,h),
                centers(5,135,220,2000,h)]
        timer = perf_counter()
        off, on = build_masks(*axes)
        added = on&~off
        assert not np.any(off&~on)
        assert np.any(added)
        i,j,k = np.where(added)
        bounds = [[float(a[q].min()),float(a[q].max())] for a,q in zip(axes,(i,j,k))]
        t = mesh_triangles("upper_blade")
        assert np.all(np.array(bounds)[:,0]>=t.min(axis=(0,1))-h)
        assert np.all(np.array(bounds)[:,1]<=t.max(axis=(0,1))+h)
        for q,b in [((560,680,230),True),((500,600,5),False),((240,30,410),True),((950,25,110),False)]:
            idx=tuple(np.abs(a-r).argmin() for a,r in zip(axes,q))
            assert bool(off[idx]) is b, (q,idx,off[idx])
        results.append(dict(spacings_mm=[h*1.5,h,h], sizes=[len(a) for a in axes],
            common_obstacle_cells=int(off.sum()), blade_only_cells=int(added.sum()),
            blade_only_cell_center_bounds_xyz_mm=bounds, elapsed_seconds=perf_counter()-timer))
    report={"native_mesh_comparison":native,"nonuniform_mask_checks":results,
        "geometry_meshes_npz_sha256":sha256((HERE/"geometry_meshes.npz").read_bytes()).hexdigest()}
    print(json.dumps(report,indent=2))
    (HERE/"geometry_validation.json").write_text(json.dumps(report,indent=2)+"\n")


if __name__ == "__main__":
    main()
