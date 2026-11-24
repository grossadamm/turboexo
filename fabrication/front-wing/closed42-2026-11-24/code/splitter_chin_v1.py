"""Separate splitter and chin designed against the V4 fiberglass in car-frame mm."""
import json
from pathlib import Path
import numpy as np
import cadquery as cq
import trimesh
from scipy.interpolate import splprep, splev
from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
from OCP.BRepCheck import BRepCheck_Analyzer

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/splitter_chin_v1'
DECK_TOP=85.
DECK_THICKNESS=6.
GAP=3.5
TOP_INSET=9.
WALL=4.
def vec(p):return cq.Vector(*map(float,p))
def line(a,b):return cq.Edge.makeLine(vec(a),vec(b))
def bezier(*pts):return cq.Edge.makeBezier([vec(p) for p in pts])
def rail():
    mid=np.loadtxt(ROOT/'grid/lip_lower_photo_break_mm.csv',delimiter=',',skiprows=1)
    arrays=[]
    for name,sign in [('right',-1),('left',1)]:
        edge=np.asarray(json.loads((ROOT/f'grid/{name}_turn_trace.json').read_text())['lower'])
        edge=edge[(sign*edge[:,1]>228)&(edge[:,0]>=-145)]
        arrays.append(edge[np.argsort(edge[:,1])])
    points=np.vstack((arrays[0],mid[abs(mid[:,1])<=225,:3],arrays[1]))
    length=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points[:,:2],axis=0),axis=1))]
    return splprep(points[:,:2].T,u=length,s=len(points)*.45**2,k=3)[0],length[-1]

def underside_sampler():
    # Test the exported shell along true vertical rays, keeping the lowest skin.
    mesh=trimesh.load(ROOT/'deliverables/body/fiberglass_adapter_reference_v3_mm.stl',process=False)
    def height(xy):
        origins=np.c_[xy,np.zeros(len(xy))]
        dirs=np.tile([0.,0.,1.],(len(xy),1))
        locations,ray,_=mesh.ray.intersects_location(origins,dirs,multiple_hits=True)
        heights=np.full(len(xy),np.inf);np.minimum.at(heights,ray,locations[:,2])
        assert np.isfinite(heights).all(),xy[~np.isfinite(heights)]
        return heights
    return height
def sections(n=43):
    spline,length=rail()
    s=np.linspace(0,length,n)
    xy=np.array(splev(s,spline)).T
    tangent=np.array(splev(s,spline,der=1)).T
    tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    outward=np.c_[tangent[:,1],-tangent[:,0]]
    outer=xy-TOP_INSET*outward;inner=outer-WALL*outward
    h=underside_sampler();zo=h(outer)-GAP;zi=h(inner)-GAP
    # Lower side returns flare gently onto the deck, within the two mounts.
    base=24+22*(abs(xy[:,1])/345)**2
    return outer,outward,zo,zi,base
def profile(top,n,zo,zi,f):
    def P(r,z):return top[0]+r*n[0],top[1]+r*n[1],z
    z=DECK_TOP;h=zo-z
    return [
        [P(0,zo),P(0,zo-h*.23),P(f-2,z+h*.34),P(f,z+13)],
        [P(f,z+13),P(f+.4,z+9),P(f+.8,z+5),P(f+6,z+3)],
        [P(f+6,z+3),P(f+7.5,z+2.4),P(f+7.5,z+.8),P(f+7.5,z)],
        [P(f+7.5,z),P(f-30,z)],
        [P(f-30,z),P(f-30,z+4.5)],
        [P(f-30,z+4.5),P(f-10,z+4.5)],
        [P(f-10,z+4.5),P(f-6.2,z+4.5),P(f-4.5,z+7.2),P(f-4,z+13)],
        [P(f-4,z+13),P(f-6,z+h*.34),P(-WALL,zi-h*.23),P(-WALL,zi)],
        [P(-WALL,zi),P(0,zo)]]
def swept_solid(profiles, station_parameters=None):
    # Interpolate each corresponding Bezier control point in the same rail
    # parameter. This keeps the wall, flange and top edge aligned at the turns.
    from scipy.interpolate import make_interp_spline
    from OCP.Geom import Geom_BSplineSurface
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_Sewing
    from OCP.TColgp import TColgp_Array2OfPnt
    from OCP.gp import gp_Pnt
    from adapter_surface import knot_vector
    u=np.linspace(0,1,len(profiles)) if station_parameters is None else station_parameters
    sew=BRepBuilderAPI_Sewing(1e-6)
    for curves in zip(*profiles):
        sp=make_interp_spline(u,np.array(curves),k=3)
        control=sp.c
        n,m=control.shape[:2]
        poles=TColgp_Array2OfPnt(1,n,1,m)
        for i,row in enumerate(control,1):
            for j,xyz in enumerate(row,1):poles.SetValue(i,j,gp_Pnt(*xyz))
        uk,um=knot_vector(sp.t);vk,vm=knot_vector([0]*m+[1]*m)
        surf=Geom_BSplineSurface(poles,uk,vk,um,vm,3,m-1)
        face=cq.Face(BRepBuilderAPI_MakeFace(surf,1e-7).Face())
        if np.ptp(control[:,:,2])<1e-6:
            flat=cq.Face.makeFromWires(face.outerWire())
            if flat.normalAt().dot(face.normalAt())<0:flat=cq.Face(flat.wrapped.Reversed())
            face=flat
        sew.Add(face.wrapped)
    for idx in [0,-1]:
        w=cq.Wire.assembleEdges([line(*c) if len(c)==2 else bezier(*c) for c in profiles[idx]])
        sew.Add(cq.Face.makeFromWires(w).wrapped)
    sew.Perform()
    shells=cq.Shape.cast(sew.SewedShape()).Shells()
    assert len(shells)==1 and shells[0].Closed()
    part=cq.Solid.makeSolid(shells[0])
    if part.Volume()<0:part=cq.Solid(part.wrapped.Reversed())
    assert part.isValid()
    return part

def drill(shape,holes,base,height):
    for x,y,diam in holes:
        tool=cq.Solid.makeCylinder(diam/2,height,cq.Vector(x,y,base))
        shape=shape.cut(tool)
    return shape
def chin():
    o,n,zo,zi,f=sections()
    part=swept_solid([profile(*args) for args in zip(o,n,zo,zi,f)])
    # Locate flange drills on the same smooth rail with ample material on both sides.
    oo,nn,_,_,ff=sections(251);center=oo+(ff-18)[:,None]*nn
    desired=[-285,-225,-137,-48,48,137,225,285]
    holes=[]
    for y in desired:
        j=np.argmin(abs(center[:,1]-y));holes.append([*center[j],5.5])
    for j in (5,len(center)-6):holes.append([*center[j],5.5])
    result=drill(part,holes,DECK_TOP-1,8)
    assert result.isValid() and len(result.Solids())==1
    return result,np.array(holes)

def deck(holes):
    z=DECK_TOP-DECK_THICKNESS
    P=lambda x,y:(x,y,z)
    # Symmetric cubic curves keep the leading crown and corner radii tangent.
    A,B,C,D,E,F=[P(x,y) for x,y in [(122,0),(72,458),(-161,458),(-187,425),(-174,0),(-187,-425)]]
    G,H=P(-161,-458),P(72,-458)
    edges=[bezier(A,P(122,160),P(110,458),B),line(B,C),bezier(C,P(-178,458),P(-187,446),D),
           bezier(D,P(-187,300),P(-174,110),E),bezier(E,P(-174,-110),P(-187,-300),F),
           bezier(F,P(-187,-446),P(-178,-458),G),line(G,H),bezier(H,P(110,-458),P(122,-160),A)]
    wire=cq.Wire.assembleEdges(edges)
    raw=cq.Solid.extrudeLinear(wire,[],cq.Vector(0,0,DECK_THICKNESS))
    result=drill(raw,holes,z-1,DECK_THICKNESS+2)
    if result.Volume()<0:result=cq.Shape.cast(result.wrapped.Reversed())
    assert result.isValid() and len(result.Solids())==1
    return result
def export_basic():
    OUT.mkdir(exist_ok=True)
    ch,holes=chin();cq.exporters.export(ch,str(OUT/'chin_mm.step'))
    (OUT/'chin_mount_holes_mm.json').write_text(json.dumps(holes.round(4).tolist(),indent=2)+'\n')
    print('chin',ch.Volume(),len(ch.Faces()),cq.importers.importStep(str(OUT/'chin_mm.step')).val().isValid(),flush=True)
    return ch,holes
if __name__=='__main__':export_basic()
