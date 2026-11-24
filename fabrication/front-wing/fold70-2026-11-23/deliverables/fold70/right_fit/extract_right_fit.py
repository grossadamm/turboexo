"""Extract a full-scale RH clearance trial from the selected 70 mm chin."""
import hashlib
import json
from pathlib import Path
import tempfile

import cadquery as cq
import numpy as np
import trimesh
from scipy.spatial import ConvexHull
from shapely.geometry import Polygon, box

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / 'full_folded_chin_mm.step'
CUT_Y = -260.
# The flat inboard cut and the measured mounting face provide repeatable
# alternatives for the initial layer. The plate normal points outboard.
RIGHT_OUTWARD = np.array([.017116613399553747,-.9998519011513133,.0017881022999644022])

def aim_up(vector):
    return trimesh.geometry.align_vectors(vector/np.linalg.norm(vector),np.array([0.,0.,1.]))[:3,:3]

def orient(mesh):
    candidates=[]
    for name,normal in [('inboard cut',np.array([0.,-1.,0.])),('outer mounting face',-RIGHT_OUTWARD)]:
        rot=aim_up(normal)
        xyz=mesh.vertices@rot.T
        hull=xyz[ConvexHull(xyz[:,:2]).vertices,:2]
        nz=mesh.face_normals@rot[2]
        zmin=xyz[:,2].min()
        bedfaces=xyz[mesh.faces,2].max(axis=1)<zmin+.05
        contact=mesh.area_faces[bedfaces].sum()
        support=float(mesh.area_faces[(nz<-.64)&~bedfaces]@(-nz[(nz<-.64)&~bedfaces]))
        for deg in range(360):
            th=np.radians(deg)
            yaw=np.array([[np.cos(th),-np.sin(th),0],[np.sin(th),np.cos(th),0],[0,0,1]])
            xy=hull@yaw[:2,:2].T
            l,h=xy.min(0),xy.max(0)
            centered=128-(l+h)/2
            if np.ptp(xy,axis=0).max()>242: continue
            for shift in [np.array([0.,0.]),np.array([0.,4.]),np.array([4.,0.])]:
                off=centered+shift
                footprint=Polygon(xy+off).buffer(6.)
                if not box(0,0,256,256).contains(footprint) or footprint.intersects(box(0,0,18,28)):continue
                margin=float(min(*(l+off),*(256-h-off)))
                candidates.append(((int(contact>=80.),-round(support,1),round(contact,1),margin),name,deg,yaw@rot,[*off,-zmin],float(contact),support))
    if not candidates: raise ValueError('No tested bed pose has draft brim clearance')
    _,name,deg,rot,tr,area,support=max(candidates,key=lambda q:q[0])
    mesh.vertices=mesh.vertices@rot.T+tr
    return dict(bed_face=name,yaw_deg=deg,bed_contact_mm2=area,downward_projected_area_mm2=support,rotation=rot.tolist(),translation=tr)

def main():
    source=cq.importers.importStep(str(SOURCE)).val()
    bounds=source.BoundingBox()
    region=cq.Solid.makeBox(1200,600+CUT_Y,500,cq.Vector(-600,-600,0))
    solid=source.intersect(region).clean()
    assert solid.isValid() and len(solid.Solids())==1
    step=OUT/'right_fit_car_mm.step'
    cq.exporters.export(solid,str(step))
    solid=cq.importers.importStep(str(step)).val()
    assert solid.isValid() and len(solid.Solids())==1
    with tempfile.TemporaryDirectory() as tmp:
        stl=Path(tmp)/'part.stl';solid.exportStl(str(stl),tolerance=.04,angularTolerance=.08,relative=False)
        mesh=trimesh.load_mesh(stl)
    assert mesh.is_volume and mesh.body_count==1
    before=mesh.volume
    pose=orient(mesh)
    target=OUT/'right_fit_bed_mm.stl';mesh.export(target)
    check=trimesh.load_mesh(target)
    assert check.is_volume and check.body_count==1 and np.isclose(check.volume,before,rtol=1e-5) and np.ptp(check.bounds,axis=0).max()<256
    report={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'cut_y_mm':CUT_Y,'retained':'Y <= cut_y_mm (car-right, passenger side on LHD)','full_scale':True,'bounds_car_mm':[bounds.ymin,CUT_Y],'bed_extents_mm':check.extents.tolist(),'pose':pose,'section_step_sha256':hashlib.sha256(step.read_bytes()).hexdigest(),'bed_stl_sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    (OUT/'extraction.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))
if __name__=='__main__':main()
