"""Open brake scoop. Coordinates in millimeters, X forward, Y left, Z up."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from scipy.interpolate import PchipInterpolator, CubicHermiteSpline
P=Path(__file__).resolve().parent
a=json.loads((P.parent/'grid/inboard_mounts_v4_geometry.json').read_text())['left']
w=np.array(a['web_plane_anchors_xyz_mm']);A,B,C=np.linalg.solve(np.c_[w[:,:2],np.ones(3)],w[:,2])
edge=PchipInterpolator(*np.array(a['front_edge_xy_mm']).T[::-1])
# Stations are aft distances from car origin. Hold the full deck through the bracket bay; turn the rails once the outer plate clears.
s=np.array([179,188,195,203,210,219,228,238,250,263,277,290,300])
left=PchipInterpolator(s,[286.7,286.7,286.7,287,287.5,288,289,291,295,300,306.5,314,319.77])
right=PchipInterpolator(s,[451.3,450.7,450.2,449.6,449.1,448.6,448.3,448.2,448.4,450.0,454.3,460.7,466.47])
inner=PchipInterpolator(s,[18,20,21,20,18,17,17,18,20,22,20,16,12])
outer=PchipInterpolator(s,[13,10,5,3.7,3.7,4.2,7,12,17,20,22,22,21])
# Ramp follows the web plane with relief, then reduces its pitch at discharge.
def base(t,y):
    plate=-A*t+B*y+C
    start=A*edge(y)+B*y+C-1
    floor=start+.14*(t-177)
    v=(floor-plate)
    level=plate+max(0,v) if abs(v)>3 else plate+(v+3)**2/12
    lift=np.interp(t,[179,188,204,230,260,278,300],[.1,.9,2.0,2.2,2.6,3.3,3.3])
    travel=max(0,t-278)
    return level+lift-.35*(travel**2/28 if travel<14 else travel-7)
def wire(t):
    lo=float(left(t));hi=float(right(t))
    def p(y,h):return cq.Vector(-t,y,base(t,y)+h)
    edges=[]
    def line(y,h,Y,H):edges.append(cq.Edge.makeLine(p(y,h),p(Y,H)))
    def arc(y,h,ym,hm,Y,H):edges.append(cq.Edge.makeThreePointArc(p(y,h),p(ym,hm),p(Y,H)))
    th=2.4
    # Rounded inner roots and rolled crowns create a single open U section.
    h=float(inner(t))+th; k=float(outer(t))+th
    line(lo,0,lo,h);arc(lo,h,lo+1.2,h+1.2,lo+th,h)
    line(lo+th,h,lo+th,th+3)
    arc(lo+th,th+3,lo+th+.88,th+.88,lo+th+3,th)
    ys=np.linspace(lo+th+3,hi-th-3,25)
    for a,b in zip(ys,ys[1:]):line(a,th,b,th)
    arc(hi-th-3,th,hi-th-.88,th+.88,hi-th,th+3)
    line(hi-th,th+3,hi-th,k);arc(hi-th,k,hi-1.2,k+1.2,hi,k)
    line(hi,k,hi,0)
    ys=np.linspace(hi,lo,27)
    for a,b in zip(ys,ys[1:]):line(a,0,b,0)
    return cq.Wire.assembleEdges(edges)
ts=np.unique(np.r_[s,np.arange(179.,301.,3.)])
deck=cq.Solid.makeLoft([wire(t) for t in ts],True)
lip=cq.importers.importStep(str(P.parent/'inlet_form/form.step')).val()
body=deck.fuse(lip).clean()
assert body.isValid() and len(body.Solids())==1
cq.exporters.export(body,str(P/'scoop.step'))
body.exportStl(str(P/'scoop.stl'),.04,.08)
bed=body.rotate((0,0,0),(0,1,0),90);box=bed.BoundingBox()
bed.translate((-box.xmin,-box.ymin,-box.zmin)).exportStl(str(P/'P1S_scoop_mm.stl'),.04,.08)
