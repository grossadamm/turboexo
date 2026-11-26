"""Cartesian cell geometry for the right-front flow screen. Requires only NumPy."""
from functools import lru_cache
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
BUMPER_REAR = 339.2  # mm, close to aft CAD edge; caps a local partial vehicle
# Tiny deterministic ray offset avoids casting through shared CAD vertices.
_EPS = np.array([0.000137, -0.000293, 0.000411])


@lru_cache(maxsize=1)
def _packed():
    with np.load(HERE / "geometry_meshes.npz") as p:
        return {k[:-2]: p[k][p[k[:-2]+"_f"]].astype(float)
                for k in p.files if k.endswith("_v")}


def mesh_triangles(name):
    """Original cached triangulation in solver coordinates, mm."""
    return _packed()[name]


def _axes(xs, ys, zs):
    axes = tuple(np.asarray(a, dtype=float) for a in (xs, ys, zs))
    if any(a.ndim != 1 or not len(a) or not np.all(np.isfinite(a)) or np.any(np.diff(a) <= 0)
           for a in axes):
        raise ValueError("Expected three strictly increasing 1-D axes of cell centers in mm.")
    if axes[1][0] < 0:
        raise ValueError("This is car-right half-domain geometry and requires y>=0.")
    return axes


def _ray_hits(tris, us, vs):
    """Sort crossings of regular/nonregular (u,v) ray lattice in physical-space d.

    triangles shape (ntri,3,3), second axis vertices, last axis (u,v,d).
    Returns packed ray IDs and depth. Nondegenerate barycentric projection,
    independent of winding or mesh tessellation density.
    """
    ray_ids, depths = [], []
    for s in range(0, len(tris), 12000):
        t = tris[s:s+12000]
        vlo, vhi = t.min(1), t.max(1)
        us0, us1 = np.searchsorted(us, vlo[:,0]), np.searchsorted(us, vhi[:,0], side="right")
        vs0, vs1 = np.searchsorted(vs, vlo[:,1]), np.searchsorted(vs, vhi[:,1], side="right")
        wu, wv = us1-us0, vs1-vs0
        a, b = t[:,1]-t[:,0], t[:,2]-t[:,0]
        det = a[:,0]*b[:,1] - a[:,1]*b[:,0]
        take = np.flatnonzero((wu > 0) & (wv > 0) & (np.abs(det)>1e-13))
        if not len(take):
            continue
        n = wu[take]*wv[take]
        tri_idx = np.repeat(take, n)
        local = np.arange(len(tri_idx))-np.repeat(np.r_[0,np.cumsum(n[:-1])], n)
        iu = us0[tri_idx]+local//wv[tri_idx]
        iv = vs0[tri_idx]+local%wv[tri_idx]
        dx, dy = us[iu]-t[tri_idx,0,0], vs[iv]-t[tri_idx,0,1]
        p = (dx*b[tri_idx,1]-dy*b[tri_idx,0])/det[tri_idx]
        q = (dy*a[tri_idx,0]-dx*a[tri_idx,1])/det[tri_idx]
        good = (p>=0.) & (q>=0.) & (p+q<=1.)
        k = tri_idx[good]
        if len(k):
            ray_ids.append(iu[good]*len(vs)+iv[good])
            depths.append(t[k,0,2]+p[good]*a[k,2]+q[good]*b[k,2])
    if not ray_ids:
        return np.empty(0,dtype=int), np.empty(0)
    ids, ds = np.concatenate(ray_ids), np.concatenate(depths)
    order = np.lexsort((ds,ids))
    ids, ds = ids[order], ds[order]
    # Merge duplicate geometric crossings from split CAD edges. Physical
    # sheets in this model are orders of magnitude thicker than this tolerance.
    keep = np.r_[True,(ids[1:]!=ids[:-1]) | (np.diff(ds)>2e-5)]
    return ids[keep], ds[keep]


def _intervals(axes, tris, direction, mode):
    uv = tuple(i for i in range(3) if i != direction)
    u, v = (axes[i]+_EPS[i] for i in uv)
    ids, ds = _ray_hits(tris[:,:,(*uv,direction)], u, v)
    rays, first, count = np.unique(ids, return_index=True, return_counts=True)
    last = first+count-1
    if mode == "blocked_fascia":
        return uv, rays, ds[first], np.full(len(rays),BUMPER_REAR)
    if mode == "envelope":
        use = count >= 2
        return uv, rays[use], ds[first[use]], ds[last[use]]
    if mode == "solid":
        # Known closed CAD parts should intersect in pairs. Odd crossings can
        # occur at tessellation cracks/tangencies. Drop isolated hits; retain
        # paired intervals in the affected ray without spuriously filling to
        # infinity or bridging a large cavity.
        par = np.arange(len(ids)) - np.repeat(first,count)
        start = np.flatnonzero((par%2==0) & (np.arange(len(ids)) < np.repeat(last,count)))
        return uv, ids[start], ds[start], ds[start+1]
    raise ValueError(mode)


def _write(mask, axes, tris, direction, mode="solid", preserve_thin=False):
    uv, rays, near, far = _intervals(axes, tris, direction, mode)
    axis = axes[direction]
    lo = np.searchsorted(axis, near, side="left")
    hi = np.searchsorted(axis, far, side="right")
    if preserve_thin:
        # Do not lose a subcell sheet altogether. Use its nearest cell only
        # when the exact physical interval contains no cell center.
        short = (lo == hi) & (near<far)
        mid = (near+far)*0.5
        if len(axis)>1:
            lower = axis[0]-(axis[1]-axis[0])*.5
            upper = axis[-1]+(axis[-1]-axis[-2])*.5
            short &= (mid>=lower) & (mid<=upper)
        else:
            short &= (mid == axis[0])
        mid = mid[short]
        l = np.clip(lo[short]-1,0,len(axis)-1)
        r = np.clip(lo[short],0,len(axis)-1)
        best = np.where(np.abs(axis[l]-mid)<=np.abs(axis[r]-mid),l,r)
        lo[short], hi[short] = best, best+1
    canvas = mask.transpose((*uv,direction))
    nuv = len(axes[uv[1]])
    for i, a, b in zip(rays, lo, hi):
        if a<b:
            canvas[i//nuv,i%nuv,a:b] = True


def _new_mask(axes):
    return np.zeros(tuple(map(len,axes)), dtype=bool)


def _shared(axes):
    p = _packed()
    m = _new_mask(axes)
    _write(m,axes,p["bumper"],0,"blocked_fascia")
    for name in ("chin","seal"):
        for direction in (2,0):
            _write(m,axes,p[name],direction,preserve_thin=True)
    for name in ("green_web","green_brace","green_plate"):
        for direction in (2,0,1):
            _write(m,axes,p[name],direction,preserve_thin=True)
    for name in p:
        if name.startswith(("intercooler_","radiator_")):
            _write(m,axes,p[name],2)
    _write(m,axes,p["tire"],2,"envelope")
    _write(m,axes,p["wing_control"],2,"envelope",preserve_thin=True)
    return m


def build_masks(xs, ys, zs):
    """Return (blade-off, blade-on) obstacles on centers, shape (nx,ny,nz)."""
    axes = _axes(xs,ys,zs)
    off = _shared(axes)
    on = off.copy()
    _write(on,axes,mesh_triangles("upper_blade"),2,preserve_thin=True)
    return off, on


def solid_mask(xs, ys, zs, blade: bool):
    """Return one requested model obstacle mask in (rearward,outward,up) order."""
    axes = _axes(xs,ys,zs)
    mask = _shared(axes)
    if blade:
        _write(mask,axes,mesh_triangles("upper_blade"),2,preserve_thin=True)
    return mask
