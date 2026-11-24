"""One folded chin in the surveyed car frame (millimetres)."""
import json
from pathlib import Path

import cadquery as cq
import numpy as np
from OCP.BRepAlgoAPI import BRepAlgoAPI_Section
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.IntCurvesFace import IntCurvesFace_ShapeIntersector
from OCP.gp import gp_Dir, gp_Lin, gp_Pnt, gp_Trsf

from splitter_chin_v1 import swept_solid

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables/full_folded_chin'
CORNER = ROOT / 'deliverables/hidden_flange_corner/corner_mm.step'
GLASS = ROOT / 'deliverables/front_end_v9/fiberglass_v9_mm.step'
THICKNESS = 3.6
CENTER_Z = 148.5
JOIN = 414.
OUTER_JOIN = 445.
INSIDE_RADIUS = 14.
REVEAL = 2.1


def unit(v):
    return v / np.linalg.norm(v)


def ease(t):
    t = np.clip(t, 0., 1.)
    return t**3 * (10. + t * (-15. + 6.*t))


def on_plate(corner):
    plates = json.loads((ROOT / 'grid/plate_v2.json').read_text())['to_car']
    left, right = plates['left'], plates['right']
    rot = np.asarray(right['R']) @ np.asarray(left['R']).T
    shift = np.asarray(right['t']) - rot @ np.asarray(left['t'])
    matrix = np.column_stack([rot, shift])
    tr = gp_Trsf()
    tr.SetValues(*matrix.ravel())
    return cq.Shape.cast(BRepBuilderAPI_Transform(corner.wrapped, tr, True).Shape())


def cut_section(shape, y):
    face = cq.Face.makePlane(1200,1200,cq.Vector(0,y,150),cq.Vector(0,1,0))
    cut = BRepAlgoAPI_Section(shape.wrapped,face.wrapped)
    cut.Build()
    edges = cq.Shape.cast(cut.Shape()).Edges()
    assert len(edges) == 8, (y, len(edges))
    # Traverse from the upper leading tip along the two show faces and back
    # along the underside. The section of the native cylindrical fold is elliptical.
    nose = max(edges, key=lambda e:e.Center().x)
    current = max([nose.startPoint(),nose.endPoint()],key=lambda p:p.z)
    curves = []
    edges.remove(nose)
    while edges:
        edge = min(edges,key=lambda e:min((p-current).Length for p in [e.startPoint(),e.endPoint()]))
        forwards = (edge.startPoint()-current).Length < 1.e-4
        assert forwards or (edge.endPoint()-current).Length < 1.e-4
        points = np.array([p.toTuple() for p in edge.positions([0,1/3,2/3,1])])
        if not forwards: points = points[::-1]
        curves.append(bezier_through(points))
        current = edge.endPoint() if forwards else edge.startPoint()
        edges.remove(edge)
    curves.append(np.linspace(curves[-1][-1],curves[0][0],4))
    return np.array(curves)


def bezier_through(points):
    t = np.linspace(0,1,4)
    basis = np.stack([(1-t)**3,3*t*(1-t)**2,3*t**2*(1-t),t**3],axis=1)
    return np.linalg.solve(basis,points)


class LowerLip:
    def __init__(self):
        self.glass = cq.importers.importStep(str(GLASS)).val()
        self.inter = IntCurvesFace_ShapeIntersector()
        self.inter.Load(self.glass.wrapped,1.e-7)

    def hits(self, origin, direction):
        self.inter.Perform(gp_Lin(gp_Pnt(*origin),gp_Dir(*direction)),0,800)
        return np.array([self.inter.Pnt(i).Coord() for i in range(1,self.inter.NbPnt()+1)])

    def rim(self,y):
        nose = self.hits((120,y,238.6),(-1,0,0))[:,0].max()
        x = nose - 3.
        heights = [self.hits((xx,y,80),(0,0,1))[:,2].min() for xx in [x,x-THICKNESS]]
        return x,min(heights)-REVEAL


def center_profile(y, rim_x, rim_z, nose_x):
    # In the X/Z section the lower toe slopes upward by six degrees. The
    # upright leans aft by four degrees. Both sides of the bend are tangent
    # to the two straight runs and have concentric radii.
    pitch, lean = np.deg2rad([6.,4.])
    first = np.array([-np.cos(pitch),np.sin(pitch)])
    second = np.array([-np.sin(lean),np.cos(lean)])
    n1,n2 = np.array([first[1],-first[0]]),np.array([second[1],-second[0]])
    tip, rim = np.array([nose_x,CENTER_Z]),np.array([rim_x,rim_z])
    dist = np.linalg.solve(np.column_stack([first,second]),rim-tip)
    vertex = tip+first*dist[0]
    center = vertex+INSIDE_RADIUS*(n1+n2)/(1.+n1@n2)
    turn_angle = np.arccos(n1@n2)
    handle = 4./3.*np.tan(turn_angle/4.)
    def arc(rad):
        a,b = center-rad*n1,center-rad*n2
        return np.array([a,a+rad*handle*first,b-rad*handle*second,b])
    near, far = arc(INSIDE_RADIUS),arc(INSIDE_RADIUS+THICKNESS)
    rear = rim-THICKNESS*n2
    under = tip-np.array([0.,THICKNESS/np.cos(pitch)])
    line = lambda a,b:np.linspace(a,b,4)
    curves = [line(tip,near[0]),near,line(near[-1],rim),line(rim,rear),
              line(rear,far[-1]),far[::-1],line(far[0],under),line(under,tip)]
    sec = np.empty((8,4,3));sec[:,:,0] = np.array(curves)[:,:,0]
    sec[:,:,2] = np.array(curves)[:,:,1];sec[:,:,1]=y
    return sec


def level_nose(row, native_z=None):
    # Keep the front level up to a tangent handover to the descending native
    # cut edge. Smooth minimum gives an exact straight run on either side
    # of a 4 mm height window. The cubic fore/aft fade has zero slope at
    # both ends so neither the front trim nor the side fold acquires a kink.
    z = row[0,0,2] if native_z is None else native_z
    half_window = 2.
    soft = max(half_window-abs(CENTER_Z-z), 0.)
    target = min(CENTER_Z,z)-soft**2/(4.*half_window)
    dz = target-row[0,0,2]
    row[0,:,2] += dz*np.array([1.,1.,0.,0.])
    row[6,:,2] += dz*np.array([0.,0.,1.,1.])
    row[7,:,2] += dz


def keep_outer(shape,sign):
    box = cq.Workplane('XY').box(800,300,500).translate((0,sign*(OUTER_JOIN+150),210)).val()
    return shape.intersect(box).clean()


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    left = cq.importers.importStep(str(CORNER)).val()
    sides = {-1:on_plate(left),1:left}
    lip = LowerLip()
    # Extrapolate the actual finish section and its spanwise tangent. Rather
    # than independently redrawing the outer fold, recover all eight edges
    # from the reviewed corner registered to each respective stock plate.
    anchors = {}
    for sign, shape in sides.items():
        vals = [cut_section(shape,sign*s) for s in (JOIN-1, JOIN, JOIN+1)]
        anchors[sign] = (vals[1],(vals[2]-vals[0])/2.)
    stations = np.unique(np.r_[-OUTER_JOIN, -JOIN, np.arange(-440.,441.,5.), JOIN, OUTER_JOIN])
    sections = []
    rim_data = []
    for y in stations:
        s = abs(y); sign = 1 if y>=0 else -1
        endpoint, slope = anchors[sign]
        side = endpoint+(s-JOIN)*slope
        # The center and both transition ends have zero slope and curvature
        # contribution from the opposite profile at the window boundaries.
        if s >= JOIN:
            row = cut_section(sides[sign], y) if s > JOIN else endpoint.copy()
            level_nose(row)
            sections.append(row)
            continue
        # Freeze the end of the underside trace after the fiberglass flank
        # turns sharply rearward. Continue aft at a limited tangent, then
        # hand off to the contoured side sheet over the diagonal support.
        end = 343. if sign==1 else 324.
        contact_y = sign*min(s,end)
        rim_x,rim_z = lip.rim(contact_y)
        if s>end:
            rim_x -= 1.70*(s-end)
        nose_x = 1.5+max(s-220.,0.)**2*.00046
        center = center_profile(y,rim_x,rim_z,nose_x)
        w = ease((s-(end-15.))/(JOIN-(end-15.)))
        row = (1-w)*center+w*side
        level_nose(row,side[0,0,2])
        sections.append(row)
        if s<=end-15.:rim_data.append([y,rim_x,rim_z])
    core = swept_solid(np.array(sections),(stations+OUTER_JOIN)/(2*OUTER_JOIN))
    print('core', core.isValid(), core.Volume(),flush=True)
    wings = [keep_outer(sides[sgn],sgn) for sgn in [-1,1]]
    result = core.fuse(*wings,tol=1.e-4).clean()
    print('union',len(result.Solids()),result.isValid(),flush=True)
    assert result.isValid() and len(result.Solids())==1
    output = OUT/'full_folded_chin_mm.step'
    cq.exporters.export(result,str(output))
    final = cq.importers.importStep(str(output)).val()
    assert final.isValid() and len(final.Solids())==1
    data = {'frame':'car XYZ mm; X forward, Y car-left, Z up',
            'source_left_corner':str(CORNER.relative_to(ROOT)),
            'fiberglass_reference':str(GLASS.relative_to(ROOT)),
            'uncut_plate_datums':'grid/plate_v2.json',
            'center_leading_edge_top_z_mm':CENTER_Z,
            'center_toe_pitch_deg':6.,'center_upright_aft_lean_deg':4.,
            'center_inside_bend_radius_mm':INSIDE_RADIUS,
            'normal_wall_center_mm':THICKNESS,
            'original_outer_wing_y_mm':OUTER_JOIN,
            'native_diagonal_fold_outboard_of_absolute_y_mm':JOIN,
            'vertical_rim_reveal_mm':REVEAL,
            'center_rim_samples_y_x_z_mm':rim_data,
            'bolts_per_side':['B','E'],'plate_flanges_mm':6.,
            'side_fold_inside_outside_radii_mm':[4.,7.6],
            'solid_count':len(final.Solids()),'valid_step':final.isValid()}
    (OUT/'construction_datums.json').write_text(json.dumps(data,indent=2)+'\n')
    print(output,flush=True)

def compressed_seal():
    """Trim a vertical prism of the actual rim face against the V9 underside."""
    from OCP.BRep import BRep_Tool
    from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
    from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
    from OCP.gp import gp_Vec
    from scipy.optimize import brentq
    import hashlib

    chin_path = OUT/'full_folded_chin_mm.step'
    chin = cq.importers.importStep(str(chin_path)).val()
    glass = LowerLip()
    x,z = glass.rim(0.)
    center = cq.Vertex.makeVertex(x-THICKNESS*.5,0,z-.125)
    f = min(chin.Faces(),key=lambda f:f.distance(center))
    surf = BRep_Tool.Surface_s(f.wrapped)
    low,high = -305.,325.
    def u_at(y):
        return brentq(lambda u:surf.Value(u,.5).Y()-y,0.,1.)
    ua,ub = u_at(low),u_at(high)
    va,vb = .08,.92
    land = BRepBuilderAPI_MakeFace(surf,ua,ub,va,vb,1.e-7).Face()
    stock = cq.Shape.cast(BRepPrimAPI_MakePrism(land,gp_Vec(0.,0.,12.)).Shape())
    if stock.Volume()<0:
        stock=cq.Shape.cast(stock.wrapped.Reversed())
    pt=surf.Value(.5,.5)
    witness=cq.Vector(pt.X(),pt.Y(),pt.Z()+.4)
    parts=stock.split(glass.glass).Solids()
    seal,=[s for s in parts if s.isInside(witness)]
    assert seal.isValid() and len(seal.Solids())==1
    # Preserve the exact underside while partitioning its very long trimmed
    # B-spline faces. This keeps OCCT's default mass integration stable.
    planes=[cq.Face.makePlane(1000,1000,cq.Vector(0,y,200),cq.Vector(0,1,0))
            for y in range(-290,325,20)]
    strips=seal.split(*planes).Solids()
    seal=strips[0].fuse(*strips[1:])
    assert seal.isValid() and len(seal.Solids())==1 and seal.Volume()>0.
    target=OUT/'seal_installed_mm.step'
    cq.exporters.export(seal,str(target))
    reopened=cq.importers.importStep(str(target)).val()
    assert reopened.isValid() and len(reopened.Solids())==1 and reopened.Volume()>0.
    assert abs(reopened.Volume()/reopened.Volume(1.e-8)-1.)<.01
    heights=[]
    for y in np.linspace(low+.1,high-.1,65):
        u=u_at(y)
        for v in [va+.005,.5,vb-.005]:
            p=surf.Value(u,v)
            underside=min(glass.hits((p.X(),y,100.),(0,0,1))[:,2])
            heights.append(underside-p.Z())
    info={'nominal_installed_compressed_seal':str(target.name),
          'source_rigid_step_sha256':hashlib.sha256(chin_path.read_bytes()).hexdigest(),
          'span_y_mm':[low,high],'cross_section_rim_fraction':[va,vb],
          'reopened_volume_mm3_default':reopened.Volume(),
          'reopened_volume_mm3_refined':reopened.Volume(1.e-8),
          'nominal_band_width_in_XZ_mm':THICKNESS*(vb-va),
          'sampled_vertical_height_mm':[min(heights),max(heights)],
          'construction':'Actual rim face extruded vertically and split by installed V9 shell. Lower piece contains witness between lip and underside.'}
    data_file=OUT/'construction_datums.json'
    data=json.loads(data_file.read_text());data['seal']=info
    data_file.write_text(json.dumps(data,indent=2)+'\n')
    print(target,info,flush=True)


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seal-only',action='store_true')
    args=parser.parse_args()
    if not args.seal_only:
        build()
    compressed_seal()
