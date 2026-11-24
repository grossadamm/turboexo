"""Car-left corner built from two planes, a cylindrical fold and a line/arc trim."""
import json
from pathlib import Path
import cadquery as cq
import numpy as np
from drawn_corner_mount import INNER, N, R, PLATE

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'deliverables/folded_corner'
wall=3.6
inside_radius=4.
run=30.
drop=8.
front_station_x=26.65
sheet_to_plate_gap=.6
brace_overlap_in_plan=12.
# Front edge of the surveyed diagonal at each junction in car coordinates.
brace=np.array([[-210.,280.47,169.],[-195.,458.39,110.]])
d=brace[1,:2]-brace[0,:2]; d/=np.linalg.norm(d)
e=np.array([-d[1],d[0]])
# Rear trim sits over the forward portion of the blue brace.
origin_xy=brace[1,:2]+(brace_overlap_in_plan-run)*e
gradient=np.array([-.03,-.505]); plane_height=125.
def main_z(xy):return plane_height+gradient@(xy-np.array([8.,465.]))
origin=np.r_[origin_xy,main_z(origin_xy)]
axis=np.r_[d,gradient@d];axis/=np.linalg.norm(axis)
eu=np.r_[e,0.];ev=np.cross(axis,eu)
def xyz(p):return cq.Vector(*(origin+eu*p[0]+ev*p[1]-500.*axis))
def line(a,b):return cq.Edge.makeLine(a,b)
def arc(a,b,c):return cq.Edge.makeThreePointArc(a,b,c)
def unit(a):return np.array(a)/np.linalg.norm(a)
def section(under=False):
    pre=(gradient@e)/np.hypot(1.,gradient@d)
    post=-(drop/run)/np.hypot(1.,gradient@d)
    n1=unit([-pre,1]);n2=unit([-post,1])
    outer=inside_radius+wall
    center=np.linalg.solve(np.stack([n1,n2]),[-outer,-outer])
    def chain(rad,offset):
        start=np.array([-400.,pre*(-400.)-offset*np.hypot(1.,pre)])
        end=np.array([70.,post*70.-offset*np.hypot(1.,post)])
        a,b=center+rad*n1,center+rad*n2
        return start,a,center+rad*unit(n1+n2),b,end
    t=chain(outer,0.);b=chain(inside_radius,wall)
    if under:
        edges=[line(xyz(b[0]),xyz(b[1])),arc(xyz(b[1]),xyz(b[2]),xyz(b[3])),line(xyz(b[3]),xyz(b[4]))]
        last=b[4]
        for p in [[70.,-550.],[-400.,-550.],b[0]]:
            edges.append(line(xyz(last),xyz(p)));last=p
    else:
        edges=[line(xyz(t[0]),xyz(t[1])),arc(xyz(t[1]),xyz(t[2]),xyz(t[3])),line(xyz(t[3]),xyz(t[4])),
               line(xyz(t[4]),xyz(b[4])),line(xyz(b[4]),xyz(b[3])),arc(xyz(b[3]),xyz(b[2]),xyz(b[1])),
               line(xyz(b[1]),xyz(b[0])),line(xyz(b[0]),xyz(t[0]))]
    return cq.Solid.extrudeLinear(cq.Wire.assembleEdges(edges),[],cq.Vector(*(1000.*axis)))
# Bumper-side plan follows two straight runs tangent to one circular roll.
m1,m2=-.12,-2.55
s1=np.array([m1,1.]);s2=np.array([m2,1.])
n1=unit([1.,-m1]);n2=unit([1.,-m2])
rad=67.;T=np.array([-61.8,268.]);C=T-rad*n1
def pos(r,n):return C+r*n
def at_y(p,s,y):return p+(y-p[1])*s
def xyvec(p):return cq.Vector(*p,65.)
def plan_line(a,b):return line(xyvec(a),xyvec(b))
def plan_arc(a,b,c):return arc(xyvec(a),xyvec(b),xyvec(c))
def prism(edges,height):
    return cq.Solid.extrudeLinear(cq.Wire.assembleEdges(edges),[],cq.Vector(0,0,height))
def inner_path(r,y0,y1):
    start,end=pos(r,n1),pos(r,n2)
    p0,p1=at_y(start,s1,y0),at_y(end,s2,y1)
    return p0,p1,[plan_line(p0,start),plan_arc(start,pos(r,unit(n1+n2)),end),plan_line(end,p1)]
def make_panel(plate_gap=sheet_to_plate_gap):
    ref=origin_xy+run*e
    def back_x(y):return ref[0]+(y-ref[1])*d[0]/d[1]
    far=pos(rad,n2); yy=(back_x(0)-far[0]+m2*far[1])/(m2-d[0]/d[1])
    A,B,inner=inner_path(rad,255.,yy)
    front_dir=unit([.69,1.])
    tangent=at_y(A,np.array([.69,1.]),300.)
    # Front station is the photo-outline option at the plate inner face.
    end=np.array([front_station_x,465.8]);vec=end-tangent
    fn=np.array([-front_dir[1],front_dir[0]])
    front_radius=np.dot(vec,vec)/(2*np.dot(vec,fn))
    fc=tangent+front_radius*fn
    mid=fc+front_radius*unit(unit(tangent-fc)+unit(end-fc))
    ext=fc+front_radius*unit(end-fc)
    et=unit([-(end-fc)[1],(end-fc)[0]])
    E=at_y(ext,et/et[1],485.)
    back=np.array([back_x(E[1]),E[1]])
    trim=prism(inner+[plan_line(B,back),plan_line(back,E),plan_line(E,end),
                      plan_arc(end,mid,tangent),plan_line(tangent,A)],260.)
    p,q,one=inner_path(rad,240.,385.)
    a,b,two=inner_path(rad+wall,240.,385.)
    ribbon=prism(one+[plan_line(q,b)]+[ed.reverse() for ed in reversed(two)]+[plan_line(a,p)],237.-65.).intersect(trim)
    folded=section().intersect(trim)
    panel=folded.fuse(ribbon.cut(section(True))).clean()
    # Trim the sheet a half millimeter inside the actual angled plate.
    plateplane=cq.Plane(origin=tuple(INNER-plate_gap*N),xDir=tuple(R[:,0]),normal=tuple(N))
    keep=cq.Workplane(plateplane).rect(1000,1000).extrude(-1000).val()
    panel=panel.intersect(keep).clean()
    return panel,front_radius

def make_corner():
    panel,front_radius=make_panel()
    # Integral tabs mate directly to the stock holes. One stands above the
    # lowered panel; the other descends from it.
    plane=cq.Plane(origin=tuple(INNER),xDir=tuple(R[:,0]),normal=tuple(N))
    holes=[]
    for name in ['upper','B']:
        u,v=PLATE['holes'][name]['uv']; ctr=INNER+R[:,0]*u+R[:,1]*v
        lo=min(v-8.5,v+(main_z(ctr[:2])-ctr[2])-6)
        hi=max(v+8.5,v+(main_z(ctr[:2])-ctr[2])+2.5)
        lug=cq.Workplane(plane).center(u,(lo+hi)/2).rect(18.,hi-lo).extrude(-7.).val()
        # Round the mounting pad corners in the plane of the steel.
        along=[ed for ed in lug.Edges() if abs(ed.tangentAt().dot(cq.Vector(*N)))>.999]
        lug=lug.fillet(3.,along)
        panel=panel.fuse(lug)
        tool=cq.Solid.makeCylinder(3.4,12,cq.Vector(*(ctr+N)),cq.Vector(*(-N)))
        holes.append(tool)
    for tool in holes:panel=panel.cut(tool)
    panel=panel.clean()
    assert panel.isValid() and len(panel.Solids())==1
    OUT.mkdir(exist_ok=True)
    cq.exporters.export(panel,str(OUT/'corner_mm.step'))
    info={'inside_radius_mm':inside_radius,'outside_radius_mm':inside_radius+wall,'thickness_mm':wall,'recess_run_in_plan_mm':run,'rearward_drop_at_equal_brace_station_mm':drop,'main_plane_dz_dx_dz_dy':gradient.tolist(),'side_sheet_relief_mm':sheet_to_plate_gap,'bumper_plan_bend_radius_mm':rad,'front_trim_radius_mm':front_radius,'front_station_nominal_x_mm':front_station_x,'brace_front_endpoints_xyz_mm':brace.tolist(),'rear_trim_offset_behind_brace_front_mm':brace_overlap_in_plan,'fold_axis_unit':axis.tolist(),'crease_intersection_xyz_mm':origin.tolist(),'valid':panel.isValid(),'faces':[f.geomType() for f in panel.Faces()]}
    (OUT/'design_parameters.json').write_text(json.dumps(info,indent=2))
    print(info,flush=True)
if __name__=='__main__':make_corner()
