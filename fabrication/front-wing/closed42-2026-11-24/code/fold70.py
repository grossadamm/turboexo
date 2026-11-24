"""Full-width 70 mm faceted bow, with a true R120 plan trim through the toe."""
import json
import cadquery as cq
import numpy as np
import full_folded_chin as old
from folded_corner import section, INNER, N, R
from splitter_chin_v1 import swept_solid

OUT=old.ROOT/'deliverables/fold70'
TIP_R=np.array([-464.31351,26.50699]) # Y, X in car-frame mm
TIP_L=np.array([465.81702,26.65078])
CENTER=(TIP_R[0]+TIP_L[0])/2
HALF=(TIP_L[0]-TIP_R[0])/2
LEAD=70.
RAD=120.
def chord(y):
    return TIP_R[1]+(TIP_L[1]-TIP_R[1])*(y-TIP_R[0])/(TIP_L[0]-TIP_R[0])

def trace():
    ys=np.array([-550,-HALF+82,-90,90,HALF-82,550])+CENTER
    points=np.c_[ys,chord(ys)+[0,0,LEAD,LEAD,0,0]]
    wire=[];samples=[points[0]];last=points[0]
    def vec(p):return cq.Vector(p[1],p[0],60.)
    def straight(a,b):wire.append(cq.Edge.makeLine(vec(a),vec(b)))
    for p,q,t in zip(points,points[1:],points[2:]):
        f=old.unit(q-p);g=old.unit(t-q);a=np.arctan2(f[0]*g[1]-f[1]*g[0],f@g)
        back=RAD*np.tan(abs(a)/2);l=q-back*f;r=q+back*g
        normal=np.sign(a)*np.array([-f[1],f[0]]);c=l+RAD*normal;v=l-c
        def at(theta):return c+np.array([v[0]*np.cos(theta)-v[1]*np.sin(theta),v[0]*np.sin(theta)+v[1]*np.cos(theta)])
        straight(last,l);wire.append(cq.Edge.makeThreePointArc(vec(l),vec(at(a/2)),vec(r)))
        samples.extend(at(s) for s in np.linspace(0,a,101));last=r
    straight(last,points[-1]);samples.append(points[-1])
    for a,b in zip([points[-1],[points[-1,0],-500],[points[0,0],-500]],[[points[-1,0],-500],[points[0,0],-500],points[0]]):straight(a,b)
    clip=cq.Solid.extrudeLinear(cq.Wire.assembleEdges(wire),[],cq.Vector(0,0,350))
    return np.array(samples),clip,points

def build():
    tr,clip,pts=trace()
    left=cq.importers.importStep(str(old.CORNER)).val()
    # Continue the two native outer sheet faces forward to reach the terminal flats.
    stock=cq.Workplane('XY').box(64,140,260).translate((15,465,193)).val()
    keep=cq.Workplane(cq.Plane(origin=tuple(INNER),xDir=tuple(R[:,0]),normal=tuple(N))).rect(1000,1000).extrude(-1000).val()
    left=left.fuse(section().intersect(stock).intersect(keep)).clean()
    outer_stock=cq.Workplane("XY").box(600,1400,500).translate((-271.,0,190.)).val()
    sides={1:left.intersect(outer_stock).clean(),-1:old.on_plate(left).intersect(outer_stock).clean()}
    lip=old.LowerLip();rows=[];anchors={}
    for sign,s in sides.items():
        vals=[old.cut_section(s,sign*y) for y in (old.JOIN-1,old.JOIN,old.JOIN+1)]
        anchors[sign]=vals[1],(vals[2]-vals[0])/2
    stations=np.unique(np.r_[-old.OUTER_JOIN,-old.JOIN,np.arange(-440.,441.,5.),old.JOIN,old.OUTER_JOIN])
    for y in stations:
        s=abs(y);sign=1 if y>=0 else -1
        endpoint,slope=anchors[sign]; side=endpoint+(s-old.JOIN)*slope
        if s>=old.JOIN:
            row=old.cut_section(sides[sign],y) if s>old.JOIN else endpoint.copy()
            old.level_nose(row)
        else:
            end=343. if sign==1 else 324.
            x,z=lip.rim(sign*min(s,end))
            x-=1.7*max(0.,s-end)
            # Small machining allowance across the four bends. An exact
            # cylindrical plan cutter below supplies the finished R120 edges.
            nominal=np.interp(y,tr[:,0],tr[:,1])
            blend=old.ease((s-390.)/(old.JOIN-390.))
            allowance=.6*(1-blend)+(29.-nominal)*blend
            desired=nominal+allowance
            center=old.center_profile(y,x,z,desired)
            w=old.ease((s-(end-15.))/(old.JOIN-(end-15.)))
            row=(1-w)*center+w*side
            dx=desired-row[0,0,0]
            row[0,:,0]+=dx*np.array([1,1,0,0]);row[6,:,0]+=dx*np.array([0,0,1,1]);row[7,:,0]+=dx
            old.level_nose(row,side[0,0,2])
            # Correct height at the finish trim of the central straight toe.
            dz=allowance*np.tan(np.deg2rad(6))*(1-old.ease((s-300)/90.))
            row[0,:,2]-=dz*np.array([1,1,0,0]);row[6,:,2]-=dz*np.array([0,0,1,1]);row[7,:,2]-=dz
        rows.append(row)
    core=swept_solid(np.array(rows),(stations+old.OUTER_JOIN)/(2*old.OUTER_JOIN))
    print("core",core.isValid(),len(core.Solids()),flush=True)
    wings=[old.keep_outer(sides[sign],sign) for sign in [-1,1]]
    joined=core.fuse(*wings,tol=1.e-4).clean()
    print("join",joined.isValid(),len(joined.Solids()),flush=True)
    part=joined.intersect(clip).clean()
    print("trim",part.isValid(),len(part.Solids()),flush=True)
    assert len(part.Solids())==1 and part.isValid()
    path=OUT/'full_folded_chin_mm.step';cq.exporters.export(part,str(path))
    check=cq.importers.importStep(str(path)).val()
    assert check.isValid() and len(check.Solids())==1
    (OUT/'plan_datums.json').write_text(json.dumps({'center_lead_mm':LEAD,'tangent_plan_radius_mm':RAD,'tip_yx_mm':[TIP_R.tolist(),TIP_L.tolist()],'virtual_shoulder_and_center_corners_yx_mm':pts[1:-1].tolist()},indent=2)+'\n')
if __name__=='__main__':build()
