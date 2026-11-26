"""Cut the installed right-wing STL in the car fore/aft plane and build solver links."""
from pathlib import Path
import argparse, hashlib, json, struct
import numpy as np
import shapely as sh
import trimesh

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "faired42_wing" / "wing_right.stl"
Y = -555.
XY = (-350., 770., 0., 470.) # aft distance then height
E = np.array([[0,0],[1,0],[0,1],[-1,0],[0,-1],[1,1],[-1,1],[-1,-1],[1,-1]])
def section(stl, y=Y):
    mesh = trimesh.load_mesh(stl)
    assert mesh.is_watertight
    segs = trimesh.intersections.mesh_plane(mesh, [0,1,0], [0,y,0])[:,:,[0,2]]*[-1,1]
    lines = sh.get_parts(sh.line_merge(sh.MultiLineString(np.round(segs,6).tolist())))
    assert all(li.is_ring for li in lines)
    contours = sorted(map(sh.Polygon, lines), key=lambda p:-p.area)
    assert all(p.is_valid for p in contours)
    return contours

def extract():
    contours=section(SRC)
    base=contours[0]
    outside=[p for p in contours[1:] if not base.contains(p)]
    cavities=[p for p in contours[1:] if base.contains(p)]
    assert len(outside)==1 and len(cavities)==5 and not base.intersects(outside[0])
    blade=outside[0]
    controls = HERE.parent / "blade_off_cad" / "wing_right.stl"
    audit = {"source": str(SRC), "sha256": hashlib.sha256(SRC.read_bytes()).hexdigest(), "car_Y_mm":Y, "orientation": "X_plot=-car_X (positive aft); Z_plot=car_Z (positive up); road Z=0", "base_bounds_aft_z_mm":list(base.bounds), "blade_bounds_aft_z_mm":list(blade.bounds), "filled_internal_cavities":len(cavities), "base_area_mm2":base.area, "blade_area_mm2":blade.area, "base_blade_min_gap_mm":base.distance(blade)}
    if controls.exists():
        exterior=section(controls)[0]
        audit["comparison_with_regenerated_blade_off"] = {"hausdorff_mm":base.hausdorff_distance(exterior),"symmetric_difference_mm2":base.symmetric_difference(exterior).area}
    (HERE/"section_profiles.json").write_text(json.dumps({"base":list(base.exterior.coords),"blade":list(blade.exterior.coords),"audit":audit},indent=2)+"\n")
    print(audit, flush=True)
    return base,blade

def build(name, grid, shape):
    xmin,xmax,zmin,zmax=XY
    nx,nz=round((xmax-xmin)/grid),round((zmax-zmin)/grid)
    z,x=np.mgrid[:nz,:nx]
    x=xmin+(x+.5)*grid
    z=zmin+(z+.5)*grid
    mask=sh.contains_xy(shape,x,z)
    near=sh.dwithin(sh.points(x,z),shape.boundary,1.415*grid)
    j,i=np.where(near & ~mask)
    src=np.column_stack((x[j,i],z[j,i]))
    if name=="empty":
        mask[:]=False
    ids=[]
    for k,(ex,ez) in enumerate(E[1:],1):
        ray=sh.linestrings(np.stack((src,src-grid*E[k]),axis=1))
        hits=sh.intersection(ray,shape.boundary)
        parts,indices=sh.get_parts(hits,return_index=True)
        hit_xy,part_index=sh.get_coordinates(parts,return_index=True)
        indices=indices[part_index]
        rr=np.linalg.norm(hit_xy-src[indices],axis=1)/(grid*np.linalg.norm(E[k]))
        q=np.full(len(j),np.inf)
        np.minimum.at(q,indices,rr)
        struck=np.isfinite(q)
        assert np.all((~mask[j-ez,i-ex]) | struck)
        ids.extend(zip(j[struck]*nx+i[struck], np.full(struck.sum(),k), np.clip(q[struck],.001,.999), strict=True))
    # Guard the short-link stencil x+e where a different link to solid blocks it.
    lookup={(p,k):q for p,k,q in ids}
    opposite=[0,3,4,1,2,7,8,5,6]
    fallback=0
    for n,(p,k,q) in enumerate(ids):
        if (p,opposite[k]) in lookup and q<.5:
            ids[n]=(p,k,.5)
            fallback+=1
    links = np.array(ids,dtype=[("p","<i4"),("k","<i4"),("q","<f4")])
    links.sort(order=["p","k"])
    with (HERE/f"{name}_{grid:g}.grid").open("wb") as f:
        f.write(struct.pack("<iiddd",nx,nz,grid,xmin,zmin))
        f.write(struct.pack("<i",len(links)))
        mask.astype(np.uint8).tofile(f)
        links.tofile(f)
    print(name,grid,nx,nz,"solid cells",int(mask.sum()),"links",len(links),"short-link fallbacks",fallback,flush=True)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("res",nargs="+",type=float)
    a=p.parse_args()
    base,blade=extract()
    for res in a.res:
        build("on",res,sh.MultiPolygon([base,blade]))
        build("off",res,base)
        build("empty",res,sh.Polygon())
