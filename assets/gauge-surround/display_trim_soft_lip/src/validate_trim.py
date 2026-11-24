"""Check the exported STEP/STLs against the approved surround and OEM CAD."""
import hashlib
import json
from xml.etree import ElementTree as ET
from zipfile import ZipFile

import cadquery as cq
import numpy as np
import trimesh

import build_trim as m
from build_trim import lbox, lcyl, lhex, OUT, APPROVED, REF, HOLES, HOLE_X, HOLE_Y
from hardware import cyl_axes
from params import HOLE_NAMES, model_to_local
from service import component_boxes, display_sweep, SERVICE_PATH

# Angle in degrees about X near the lower screen rail, then local X/Y/Z offsets.
# The tiny X bias is toward viewer-right. Reverse the curve for installation.
PIVOT_Y = -52.7
TRIM_PATH = [
    (0.,0.,0.,0.), (4.,.3,.3,.02), (7.,.5,.65,.08), (10.,.6,1.1,.20),
    (10.,.75,2.5,.48), (10.,.87,3.,.85), (10.,1.06,4.,1.5), (10.,.95,5.,2.4),
    (10.,.80,6.,3.8), (10.,.65,7.,5.8), (10.,.58,8.,7.8), (10.,.50,10.,15.),
    (10.,0.,10.,25.), (10.,0.,10.,75.),
]
EPS = 1e-5


def volume(a,b):
    return max(0.,float(a.intersect(b).Volume()))


def box_bounds(shape):
    box = shape.BoundingBox()
    return [[box.xmin,box.ymin,box.zmin],[box.xmax,box.ymax,box.zmax]]


def view_frustum(eye, margin):
    a, b = m.ACTIVE_W/2+margin, m.ACTIVE_H/2+margin
    corners = np.array([[m.ACTIVE_CX+x,y,0.] for x,y in ((-a,-b),(a,-b),(a,b),(-a,b))])
    end = corners + [0.,0.,150.] if eye is None else .998*np.asarray(eye)+.002*corners
    wires = [cq.Wire.makePolygon([cq.Vector(*p) for p in (*ring,ring[0])]) for ring in (corners,end)]
    return cq.Solid.makeLoft(wires, ruled=True)


def check_hardware(base, trim, lcd, frame):
    result = {}
    metal_front = {HOLE_NAMES[sx,sy]:min((face for face in frame.Faces()
                  if face.geomType()=="PLANE" and abs(face.Center().z-m.LUG_FACE_Z)<EPS),
                  key=lambda f:(f.Center()-cq.Vector(sx*HOLE_X,sy*HOLE_Y,m.LUG_FACE_Z)).Length)
                  for sx,sy in HOLES}
    for sx,sy in HOLES:
        x,y = sx*HOLE_X,sy*HOLE_Y
        name = HOLE_NAMES[sx,sy]
        pieces = m.fasteners(x,y)
        axes = {}
        for label,shape,diameter in (("fascia",trim,m.BORE_D),("metal_lug",frame,3.5),("surround",base,3.4)):
            hits = [(float(np.linalg.norm(np.cross(np.array([x,y,0.])-p,v))),float(abs(v[2])))
                    for p,v in cyl_axes(shape,diameter/2,.002)]
            axes[label] = min(distance for distance,alignment in hits if alignment>.999)
        trim_faces = [f for f in trim.Faces() if f.geomType()=="PLANE"
                      and abs(f.Center().z-m.LUG_FACE_Z)<EPS and abs(f.Center().x-x)<4
                      and abs(f.Center().y-y)<4]
        contact = sum(f.intersect(metal_front[name]).Area() for f in trim_faces)
        assert all(e<EPS for e in axes.values()) and contact > 20.
        assert abs(contact-sum(f.Area() for f in trim_faces))<EPS
        land_ref = lcyl(x,y,m.FACE_Z,m.FACE_Z+.1,m.WASHER_D).cut(
            lcyl(x,y,m.FACE_Z-.1,m.FACE_Z+.2,3.2))
        land_from_washer = min(land_ref.Faces(),key=lambda f:f.Center().z)
        counterfaces = [f for f in trim.Faces() if f.geomType()=="PLANE" and abs(f.Center().z-m.FACE_Z)<EPS]
        flat_bearing_area = sum(land_from_washer.intersect(f).Area() for f in counterfaces)
        assert flat_bearing_area > 15.
        slide_end = sx*(137. if name == "bottom_left" else 112.)
        nut_route = lbox(*sorted((x,slide_end)),y-2.75,y+2.75,m.NUT_BACK,m.NUT_FACE).fuse(
            lhex(x,y,m.NUT_BACK,m.NUT_FACE,5.5), lhex(slide_end,y,m.NUT_BACK,m.NUT_FACE,5.5))
        inserts = {
            **pieces,
            "6.25 mm washer and driver approach":lcyl(x,y,m.FACE_Z+.001,110.,6.25),
            "side loaded nut travel":nut_route,
            "screw insertion shank path":lcyl(x,y,m.TIP_Z,110.,3.),
        }
        overlap = {k:{n:volume(s,t) for n,t in (("base",base),("LCD",lcd),("trim",trim))}
                   for k,s in inserts.items()}
        assert max(v for group in overlap.values() for v in group.values()) < EPS, (name,overlap)
        # Model a +0.5 mm length screw and a 0.05 mm thinner washer together.
        long_tip = lcyl(x,y,m.TIP_Z-.55,m.NUT_FACE,3.)
        assert volume(base,long_tip)<EPS
        axis_beyond = lcyl(x,y,-90.,m.TIP_Z,3.).intersect(base)
        first_hard_stop = max((s.BoundingBox().zmax for s in axis_beyond.Solids()
                              if s.Volume()>EPS),default=None)
        result[name] = dict(axis_error_mm=axes, lug_contact_area_mm2=contact,
            washer_contact_area_mm2=flat_bearing_area, overlaps_mm3=overlap,
            axial_clearance_beyond_tip_to_first_stop_mm=None if first_hard_stop is None
            else m.TIP_Z-first_hard_stop)
    return result


def main():
    base, lcd_parts = m.references()
    lcd = cq.Compound.makeCompound(list(lcd_parts.values()))
    frame = lcd_parts["frame_lugs"]
    trim = m.to_local(cq.importers.importStep(str(OUT/"display_trim.step")).val())
    print("Read released STEP",flush=True)
    assert trim.isValid() and len(trim.Solids())==1
    mesh_info = {}
    for filename in ("display_trim.stl","display_trim_face_down.stl"):
        mesh = trimesh.load_mesh(OUT/filename)
        assert mesh.is_watertight and mesh.is_winding_consistent and len(mesh.split())==1
        assert abs(mesh.volume/trim.Volume()-1)<.001
        mesh_info[filename] = dict(watertight=True, winding_consistent=True, components=1,
                                   bbox_mm=mesh.bounds.tolist(), volume_mm3=mesh.volume)
    with ZipFile(OUT/"display_trim_assembly.3mf") as archive:
        assert archive.testzip() is None
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
    ns = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
    objects = model.findall("m:resources/m:object", ns)
    items = model.findall("m:build/m:item", ns)
    assert len(objects)==len(items)==17
    assert [o.attrib["id"] for o in objects] == [i.attrib["objectid"] for i in items]
    for obj in objects:
        vertices = [[float(v.attrib[k]) for k in ("x","y","z")]
                    for v in obj.findall("m:mesh/m:vertices/m:vertex", ns)]
        faces = [[int(f.attrib[k]) for k in ("v1","v2","v3")]
                 for f in obj.findall("m:mesh/m:triangles/m:triangle", ns)]
        mesh = trimesh.Trimesh(vertices, faces, process=False)
        assert mesh.is_watertight and mesh.is_winding_consistent and mesh.volume>0, obj.attrib
    assy = cq.importers.importStep(str(OUT/"display_trim_assembly.step")).val()
    assert len(assy.Solids())==17 and assy.isValid()
    assembled_base = max(assy.Solids(),key=lambda solid:solid.Volume())
    approved_base = cq.importers.importStep(str(APPROVED/"surround.step")).val()
    base_difference = (approved_base.cut(assembled_base).Volume(),
                       assembled_base.cut(approved_base).Volume())
    assert max(base_difference)<EPS

    original = m.to_local(cq.importers.importStep(str(m.ORIGINAL/"display_trim.step")).val())
    original_back = m.approved_aperture_at(m.RING_BACK_Z).BoundingBox()
    original_front = m.approved_aperture_at(m.FACE_Z).BoundingBox()
    source_hashes = json.loads((m.ORIGINAL/"checkpoint.json").read_text())["deliverable_sha256"]
    assert all(hashlib.sha256((m.ORIGINAL/path).read_bytes()).hexdigest()==digest
               for path,digest in source_hashes.items())
    local_change_zone = lbox(-81.,78.,-51.,51.,m.LIP_BACK_Z-.01,m.LIP_JOIN_Z+.01)
    updated_exterior = trim.cut(local_change_zone)
    original_exterior = original.cut(local_change_zone)
    assert updated_exterior.isValid() and original_exterior.isValid()
    exterior_change = (updated_exterior.cut(original_exterior, tol=1e-6).Volume(),
                       original_exterior.cut(updated_exterior, tol=1e-6).Volume())
    assert max(exterior_change)<EPS, exterior_change

    fit = {name:dict(overlap_mm3=volume(trim,shape),distance_mm=trim.distance(shape))
           for name,shape in {"base":base,**lcd_parts}.items()}
    assert max(row["overlap_mm3"] for row in fit.values())<EPS
    assert fit["base"]["distance_mm"]>.25
    glass_gap = fit["glass_1"]["distance_mm"]
    assert .30 < glass_gap < .40 and fit["glass_2"]["distance_mm"] > .30
    margin_x = (m.LIP_APERTURE[0]-m.ACTIVE_W)/2
    margin_y = (m.LIP_APERTURE[1]-m.ACTIVE_H)/2
    profile = dict(throat_z_mm=m.LIP_THROAT_Z, throat_size_mm=m.LIP_APERTURE,
                   throat_center_mm=[m.ACTIVE_CX,m.LIP_CY], throat_plan_radius_mm=m.LIP_RADIUS,
                   rear_z_mm=m.LIP_BACK_Z, rear_opening_mm=[n+2*m.LIP_EDGE_BEVEL for n in m.LIP_APERTURE],
                   rear_chamfer_radial_mm=m.LIP_EDGE_BEVEL,
                   rear_chamfer_axial_mm=m.LIP_THROAT_Z-m.LIP_BACK_Z,
                   rear_land_width_mm=m.LIP_LAND, root_offset_from_throat_mm=m.LIP_ROOT_OFFSET,
                   blend_joins_original_at_z_mm=m.LIP_JOIN_Z,
                   approved_back_opening_mm=[original_back.xlen,original_back.ylen],
                   approved_front_opening_mm=[original_front.xlen,original_front.ylen],
                   throat_margin_active_each_edge_mm=dict(left=margin_x,right=margin_x,
                       top=margin_y+m.LIP_CY,bottom=margin_y-m.LIP_CY))
    components = list(component_boxes())
    tallest_component_z = max(hi[2] for lo,hi in components)
    proximate_components = [lbox(*(v for pair in zip(lo,hi) for v in pair))
                            for lo,hi in components if hi[2]>m.LUG_FACE_Z-.10]
    fit["frontmost_flex_bounds"] = dict(
        overlap_mm3=max(volume(trim,u) for u in proximate_components),
        distance_mm=min(trim.distance(u) for u in proximate_components))
    assert fit["frontmost_flex_bounds"]["overlap_mm3"]<EPS
    hardware = check_hardware(base,trim,lcd,frame)
    print("Checked four screw stacks and front/side access",flush=True)

    glass = {name:box_bounds(lcd_parts[name]) for name in ("glass_1","glass_2")}
    rear = max((face for face in frame.Faces() if face.geomType()=="PLANE"
               and abs(face.Center().z-m.LUG_BACK_Z)<EPS),key=lambda f:f.Area())
    exterior_mask = cq.Face.makeFromWires(m.outline(m.LUG_BACK_Z))
    uncovered = float(rear.cut(exterior_mask).Area())
    assert uncovered<.03, uncovered
    eyes = json.loads((REF/"viewpoints.json").read_text())["camera_centers"]
    eyes = {name:model_to_local(point)[0] for name,point in eyes.items()}
    screws = [piece for sx,sy in HOLES for name,piece in m.fasteners(sx*HOLE_X,sy*HOLE_Y).items()
              if name!="Retained nut"]
    obstruction = cq.Compound.makeCompound([base,trim,*screws])
    views = {}
    for name,eye in {"screen normal":None,**eyes}.items():
        cone = view_frustum(eye,.3)
        views[name] = dict(buffer_each_edge_mm=.3, overlap_mm3=volume(obstruction,cone),
                          distance_mm=obstruction.distance(cone),
                          actual_active_overlap_mm3=volume(obstruction,view_frustum(eye,0.)))
        assert views[name]["actual_active_overlap_mm3"]<EPS
        assert views[name]["overlap_mm3"] < EPS
    print("Checked complete viewing cones",flush=True)

    motion = []
    for i,(a,b) in enumerate(zip(TRIM_PATH,TRIM_PATH[1:])):
        for t in (0.,.25,.5,.75,1.) if i==0 else (.25,.5,.75,1.):
            ang,dx,dy,dz=(1-t)*np.array(a)+t*np.array(b)
            part = trim.rotate((0,PIVOT_Y,0),(1,PIVOT_Y,0),ang).translate((dx,dy,dz))
            row = dict(pose=[ang,dx,dy,dz],base_overlap_mm3=volume(part,base),
                       lcd_overlap_mm3=volume(part,lcd),base_distance_mm=part.distance(base), lcd_distance_mm=part.distance(lcd),
                       flex_overlap_mm3=max(volume(part,u) for u in proximate_components))
            assert max(row["base_overlap_mm3"],row["lcd_overlap_mm3"],row["flex_overlap_mm3"])<EPS,row
            motion.append(row)
    prior = json.loads((m.ORIGINAL/"validation.json").read_text())["fascia_motion_check"]
    assert len(prior)==len(motion)
    for old,new in zip(prior,motion):
        assert np.allclose(old["pose"],new["pose"])
        assert new["base_distance_mm"]>=old["base_distance_mm"]-EPS
    tight = min(motion,key=lambda row:row["base_distance_mm"])
    interval = next((np.array(a),np.array(b)) for a,b in zip(TRIM_PATH,TRIM_PATH[1:])
                    if a[3]<tight["pose"][3]<b[3])
    refinement = []
    for t in np.linspace(0.,1.,25):
        a,b=interval
        ang,dx,dy,dz=(1-t)*a+t*b
        def at_pose(shape):
            return shape.rotate((0,PIVOT_Y,0),(1,PIVOT_Y,0),ang).translate((dx,dy,dz))
        moved = at_pose(trim)
        dist = moved.distance(base)
        prior_dist = at_pose(original).distance(base)
        assert dist>.15 and dist >= prior_dist-EPS
        assert max(volume(moved,base),volume(moved,lcd),
                   *(volume(moved,u) for u in proximate_components))<EPS
        refinement.append(dict(pose=[ang,dx,dy,dz], base_distance_mm=dist,
                               approved_fascia_base_distance_mm=prior_dist,
                               lcd_distance_mm=moved.distance(lcd)))
    print("Checked fascia extraction poses",flush=True)
    nuts = cq.Compound.makeCompound([m.fasteners(sx*HOLE_X,sy*HOLE_Y)["Retained nut"]
                                    for sx,sy in HOLES])
    lcd_extraction = max(volume(m.to_local(s),cq.Compound.makeCompound([base,nuts])) for s in display_sweep())
    assert lcd_extraction < EPS
    approved_hashes = {f:hashlib.sha256((APPROVED/f).read_bytes()).hexdigest()
                       for f in ("surround.step","surround.stl","validation.json","model_view.html")}
    report = dict(approved_hashes=approved_hashes,trim_solid_volume_mm3=trim.Volume(),
        assembly_step_solid_count=len(assy.Solids()), assembly_3mf_object_count=len(objects),
        original_release_hashes_verified=len(source_hashes),
        difference_outside_local_lip_region_mm3=exterior_change,
        lip_profile=profile,
        assembly_export_base_symmetric_difference_mm3=base_difference,
        trim_print_meshes=mesh_info,
        installed_fit=fit,glass_bbox_local_mm=glass,
        lug=dict(front_z_mm=m.LUG_FACE_Z,back_z_mm=m.LUG_BACK_Z,thickness_mm=.6),
        rear_component_max_z_mm=tallest_component_z,
        OEM_outline_uncovered_outside_trim_silhouette_mm2=uncovered,
        viewing_cones=views,hardware=hardware,
        screw_stack=dict(fascia_mm=m.FACE_Z-m.LUG_FACE_Z,washer_mm=m.WASHER_T,
                         metal_lug_mm=.6,front_web_mm=3.,nut_mm=2.4,
                         thread_engagement_mm=2.4,tip_past_nut_mm=m.NUT_BACK-m.TIP_Z,
                         M3x8_engagement_mm=max(0., m.NUT_FACE-(m.UNDER_HEAD-8.)),
                         M3x12_engagement_mm=min(2.4,m.NUT_FACE-(m.UNDER_HEAD-12.))),
        fascia_pivot_local_y_mm=PIVOT_Y,fascia_motion_check=motion,
        fascia_tight_interval_resample=refinement,
        LCD_service_local_up_out_mm=SERVICE_PATH,
        LCD_service_swept_base_and_nut_overlap_mm3=lcd_extraction)
    (OUT/"validation.json").write_text(json.dumps(report,indent=2)+"\n")
    print("Wrote validation.json",flush=True)


if __name__=="__main__":
    main()
