from surround import *
from geom import lbox
from hardware import display_hardware, hardware_check, vol
from service import component_boxes, SERVICE_PATH
from params import (REF, ACTIVE_CX, ACTIVE_H, ACTIVE_W, R, TAB_BACK_W,
                    BODY_HALF_X, TAB_FRONT_W, local_to_model)
def section(shape, plane):
    return cq.Workplane(plane).newObject([shape]).section().val().Faces()

def S(name):
    return cq.Shape.importBrep(str(REF / 'vendor' / f'{name}.brep'))
import trimesh
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.TopAbs import TopAbs_IN
from OCP.gp import gp_Pnt

E = OUT / 'inputs'
def read(path):
    return json.loads(path.read_text())
def witness_clearance(part, xyz):
    point = cq.Vertex.makeVertex(*xyz)
    d = min(shell.distance(point) for shell in part.Shells())
    classifier = BRepClass3d_SolidClassifier(part.Solids()[0].wrapped)
    classifier.Perform(gp_Pnt(*xyz), 1e-6)
    return -d if classifier.State() == TopAbs_IN else d

def sample_segments(part):
    # Exact BRep distances from the captured eyes and 400 mm normal rays to
    # the 9 x 7 screen grid (includes the four active corners).
    grid = local_to_model([[x+ACTIVE_CX,y,0.] for x in np.linspace(-ACTIVE_W/2,ACTIVE_W/2,9)
                           for y in np.linspace(-ACTIVE_H/2,ACTIVE_H/2,7)])
    hardware = [solid for h in HOLES for name,solid in display_hardware(*h).items()
                if name in ("bolt","washer")]
    obstruction = cq.Compound.makeCompound([part,*hardware])
    endpoints = {key:np.repeat([eye],len(grid),axis=0)
                 for key,eye in read(REF/'viewpoints.json')['camera_centers'].items()}
    endpoints["screen_normal"] = grid+400*R[:,2]
    return {key:obstruction.distance(cq.Compound.makeCompound(
        [cq.Edge.makeLine(vec(a),vec(b)) for a,b in zip(grid,end)]))
        for key,end in endpoints.items()}

def stock_green_samples():
    raw=np.loadtxt(REF/'taped_scene_pointcloud.ply',skiprows=11)
    tr=read(REF/'updated_scan_transform.json')
    green=raw[:,4]-np.maximum(raw[:,3],raw[:,5])>24
    return ((raw[green,:3]-tr['origin_world'])@np.asarray(tr['rotation_rows_world_to_model']).T
             *tr['mm_per_world_unit'])

def face_ligaments(part,m):
    values=[]
    for depth in (0.,PAD_DEPTH):
        origin=m.at(n=depth)
        candidates=[f for f in part.Faces() if f.geomType()=="PLANE"
            and abs((np.asarray(f.Center().toTuple())-origin)@m.n)<1e-5
            and abs(np.asarray(f.normalAt().toTuple())@m.n)>.99999
            and f.distance(cq.Vertex.makeVertex(*origin))<4 and f.innerWires()]
        face=max(candidates,key=lambda f:f.Area())
        slot=min(face.innerWires(),key=lambda f:f.distance(cq.Vertex.makeVertex(*origin)))
        values.append(dict(depth_mm=depth, min_polymer_mm=face.outerWire().distance(slot),
                           net_washer_land_face_area_mm2=face.Area()))
    return values

def main():
    part = cq.importers.importStep(str(OUT / 'surround.step')).val()
    mesh = trimesh.load_mesh(OUT / 'surround.stl')
    lcd = cq.Compound.makeCompound([S(k) for k in ('lcd_frame_lugs','lcd_glass_1','lcd_glass_2')])
    pcb = cq.Compound.makeCompound([to_model(lbox(*[v for pair in zip(lo,hi) for v in pair]))
                                   for lo,hi in component_boxes()])
    base, mounts, supports, _ = make()
    old_scan = read(E/'shroud_check.json')['aperture']
    original_green = read(E/'green_penetration.json')
    axes, hardware = hardware_check(part, lcd)
    green_samples=stock_green_samples()
    body=lcd.intersect(to_model(lbox(-BODY_HALF_X-.01,BODY_HALF_X+.01,-60,60,-10,5)))
    retained_nuts = cq.Compound.makeCompound([display_hardware(*h)['nut'] for h in HOLES])
    root_radius_faces = [f for f in part.Faces() if f.geomType()=="CYLINDER"
                         and abs(f._geomAdaptor().Cylinder().Radius()-ROOT_RADIUS)<1e-6]
    checks = {
        'geometry': dict(valid=part.isValid(), solids=len(part.Solids()), volume=part.Volume(),
            stl_watertight=bool(mesh.is_watertight), stl_winding=bool(mesh.is_winding_consistent),
            stl_components=len(mesh.split(only_watertight=False)), stl_volume_delta_mm3=mesh.volume-part.Volume()),
        'OEM_axis_error_mm': axes, 'OEM_hardware': hardware,
        'LCD_overlap_mm3': vol(lcd,part), 'PCB_distance_mm': pcb.distance(part),
        'body_to_print_mm': body.distance(part),
        'service_waypoints_up_viewer_mm': SERVICE_PATH,
        'sweep_overlap_mm3': max(vol(part,s) for s in display_sweep()),
        'retained_nut_sweep_overlap_mm3': max(vol(retained_nuts,s) for s in display_sweep()),
        'sightline_min_clearances_mm': sample_segments(part),
        'root_blend_radius_mm': ROOT_RADIUS,
        'root_blend_face_distance_to_witness_mm': {
            key:min(f.distance(cq.Vertex.makeVertex(*pt)) for f in root_radius_faces)
            for key,pt in ROOT_BLENDS.items()
        },
        'green': {}, 'mounts': {},
    }
    print({k:v for k,v in checks.items() if k!='OEM_hardware'},flush=True)
    print('hardware overlaps', {k:max(vv['core'] for vv in v['overlaps_mm3'].values()) for k,v in hardware.items()},flush=True)
    for side,m in mounts.items():
        checks['green'][side] = [
            dict(xyz_mm=w['xyz_mm'],old_mm=-w['distance_to_STEP_boundary_mm'],
                 new_mm=witness_clearance(part,w['xyz_mm']),base_mm=witness_clearance(base,w['xyz_mm']))
            for w in original_green[side]]
        print(side,'green',checks['green'][side],flush=True)
        flange = cq.Workplane(m.axial_plane()).circle(PAD_RADIUS[side]).extrude(PAD_DEPTH).val()
        slotted = m.slot()
        sections = {}
        for h in [0, 2, 4, 6, *range(8, 49, 2)]:
            plane = m.section_plane(h)
            fs = section(supports[side].cut(slotted), plane)
            base_faces = section(supports[side].intersect(base), plane)
            sections[h] = dict(support_mm2=sorted([f.Area() for f in fs if f.Area()>.02],reverse=True),
                             shared_with_rail_mm2=sum(f.Area() for f in base_faces))
        local=(green_samples-m.center)@np.stack([m.u,m.up,m.n]).T
        region=np.all((local>=(-22,-8,-14))&(local<=(25,26,11)),axis=1)
        green_d=[witness_clearance(part,g) for g in green_samples[region]]
        tools={}
        for od,reach in TOOL_STEPS[side]:
            approach=m.access(od,PAD_DEPTH+.02,PAD_DEPTH+reach)
            # The D16 straight-envelope capture contains the smaller compact
            # shape including the shank travel for the 4 mm pin case.
            points=old_scan[side]['tool_ray']['D16x35']['witness_xyz_mm']
            tools[f'D{od}x{reach}']=dict(polymer_overlap_mm3=vol(part,approach),
                LCD_overlap_mm3=vol(lcd,approach),
                old_scan_points_in_envelope=sum(approach.isInside(vec(x),1e-6) for x in points))
        row = dict(slot_mm=[m.length,m.width], residual_slot_mm3=vol(part,slotted),
            faces=face_ligaments(part,m),
            shank_path_overlap_mm3=vol(part,m.access(4,-8,24)),
            nearby_green_point_samples=len(green_d),
            nearby_green_point_hits=int(sum(d<-.001 for d in green_d)),
            nearby_green_min_signed_mm=min(green_d,default=None),
            vehicle_face_xyz_mm=m.center.tolist(), slot_axis_driverward=m.n.tolist(),
            nominal_steel_to_polymer_gap_mm=float((m.center-np.asarray(
                SLOT_DATUMS[side]['vehicle_slot_center_mm']))@m.n),
            pad_missing_mm3=vol(part,flange)-flange.cut(slotted).Volume(),
            rail_overlap_mm3=vol(supports[side],base),
            compact_tools=tools,
            old_sample_inside=sum(witness_clearance(part,p)<-.001 for p in old_scan[side]['old_points_inside_step']),
            sections=sections)
        checks['mounts'][side]=row
        print(side,row,flush=True)
    roof, = [f for f in part.Faces() if abs(f.BoundingBox().zmin)<1e-6 and abs(f.BoundingBox().zmax)<1e-6]
    bounds = roof.BoundingBox()
    checks['roof'] = dict(edges=len(roof.Edges()), holes=len(roof.innerWires()),
                          length_mm=bounds.xlen, width_mm=bounds.ylen)
    (OUT/'validation.json').write_text(json.dumps(checks,indent=2)+'\n')
    assert checks['geometry']['valid'] and checks['geometry']['solids']==1
    assert checks['geometry']['stl_watertight'] and checks['geometry']['stl_winding']
    assert checks['geometry']['stl_components']==1
    assert abs(checks['geometry']['stl_volume_delta_mm3'])/part.Volume()<.001
    assert checks['LCD_overlap_mm3']<1e-5 and checks['PCB_distance_mm']>.99
    assert max(axes)<.05
    assert all(h['seat_plane_error_mm']<1e-5 and h['near_axis_seat_area_mm2']>45
               and all(max(x.values())<1e-5 for x in h['overlaps_mm3'].values()) for h in hardware.values())
    assert checks['sweep_overlap_mm3']<1e-5 and checks['retained_nut_sweep_overlap_mm3']<1e-5
    assert min(checks['sightline_min_clearances_mm'].values())>2
    assert checks['roof']['holes']==0 and checks['roof']['edges']==4
    assert all(e.geomType()=='LINE' for e in roof.Edges())
    assert abs(bounds.xlen-279.48)<1e-5 and abs(bounds.ylen-192.49)<1e-5
    assert min(g['new_mm'] for g in checks['green']['left'])>=2
    for row in checks['mounts'].values():
        # The driver-side relief ends on the bearing plane. At that plane,
        # preserve a minimum flat ring of 3 mm. The full 6 mm collar below
        # that plane retains the 8 - 4.2 mm polymer edge distance.
        assert row['faces'][0]['min_polymer_mm']>3.75
        assert row['faces'][1]['min_polymer_mm']>2.95
        assert abs(row['pad_missing_mm3'])<.001
        assert row['shank_path_overlap_mm3']<1e-5
        assert row['nearby_green_point_hits']==0
        assert all(t['old_scan_points_in_envelope']==0 and t['LCD_overlap_mm3']<1e-5
                   for t in row['compact_tools'].values())
        assert row['rail_overlap_mm3']>1000 and row['residual_slot_mm3']<1e-5
        assert all(x['polymer_overlap_mm3']<1e-5 for x in row['compact_tools'].values())

if __name__=='__main__':
    main()
