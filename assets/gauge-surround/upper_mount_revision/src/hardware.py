"""OEM M3 stack-up and installation checks."""
import json
import numpy as np
import cadquery as cq
import geom
import service as design
from geom import lcyl, lhex, to_model, lbox
from params import (HOLES, HOLE_NAMES, HOLE_X, HOLE_Y, P, R, REF, TAB_BACK_W,
                    TAB_FRONT_W, hole_local, local_to_model, model_to_local)

def cyl_axes(shape, r, tol=0.02):
    out = []
    for f in shape.Faces():
        if f.geomType() == 'CYLINDER':
            c = f._geomAdaptor().Cylinder()
            if abs(c.Radius() - r) < tol:
                l = c.Location(); d = c.Axis().Direction()
                out.append((np.array([l.X(), l.Y(), l.Z()]), np.array([d.X(), d.Y(), d.Z()])))
    return out


def vol(a, b):
    try:
        return float(a.intersect(b).Volume())
    except Exception as e:
        raise RuntimeError(f'boolean failed: {e}')


def display_hardware(sx, sy):
    """Returns dict name->shape (model frame). Bolt ISO4762 M3xL, DIN433 washer, ISO4032 nut."""
    hx, hy = sx * HOLE_X, sy * HOLE_Y
    wt = P['washer_t']; L = P['display_bolt_len']
    washer = lcyl(hx, hy, TAB_FRONT_W, TAB_FRONT_W + wt, P['washer_od']).cut(lcyl(hx, hy, TAB_FRONT_W - 1, TAB_FRONT_W + 1, 3.2))
    uh = TAB_FRONT_W + wt                                    # under-head plane
    bolt = lcyl(hx, hy, uh, uh + P['head_h'], P['head_d']).fuse(lcyl(hx, hy, uh - L, uh, 3.0))
    bolt = bolt.cut(lhex(hx, hy, uh + P['head_h'] - 1.8, uh + P['head_h'] + 0.1, 2.5))   # hex socket
    nf = TAB_BACK_W - P['pad_front_web']                     # nut seats on pocket face nearest tab
    nut = lhex(hx, hy, nf - P['nut_t_nom'], nf, P['nut_af_nom']).cut(lcyl(hx, hy, nf - 3, nf + 1, 3.0))
    return {'bolt': to_model(bolt), 'washer': to_model(washer), 'nut': to_model(nut)}


def display_sweeps(sx, sy):
    hx, hy = sx * HOLE_X, sy * HOLE_Y
    nf = TAB_BACK_W - P['pad_front_web']
    xs = sorted([hx, sx * 112.0])
    nut_load = lbox(xs[0], xs[1], hy - P['nut_af_nom'] / 2, hy + P['nut_af_nom'] / 2, nf - P['nut_t_nom'], nf).fuse(
        lhex(hx, hy, nf - P['nut_t_nom'], nf, P['nut_af_nom']))
    uh = TAB_FRONT_W + P['washer_t']
    tool = lcyl(hx, hy, uh, uh + 80.0, P['head_d'] + 0.5)   # head insertion + 2.5 hex key/driver column along normal
    return {'nut_load_path': to_model(nut_load), 'bolt_tool_path': to_model(tool)}


def hardware_check(core, lcd):
    axes=cyl_axes(core,P['m3_bore']/2)
    independent=json.loads((REF/'parent_mount_check.json').read_text())['points']
    z=R[:,2]
    bore_offsets=[min(float(np.linalg.norm(np.cross(np.array(p['tab_rear_hole_center_model_mm'])-c,d)))
                      for c,d in axes if abs(z@d)>.999999) for p in independent]
    report={}
    for h in HOLES:
        name=HOLE_NAMES[h]
        hc=local_to_model(hole_local(*h))[0]
        faces=[f for f in core.Faces() if f.geomType()=='PLANE' and np.linalg.norm(np.asarray(f.Center().toTuple())-hc)<12
               and np.array(f.normalAt().toTuple())@z>.999999]
        seats=[(float(model_to_local(f.Center().toTuple())[0][2]),f.Area()) for f in faces]
        area=sum(a for w,a in seats if abs(w-TAB_BACK_W)<.0001)
        hw=display_hardware(*h)
        motion=display_sweeps(*h)
        if name=='bottom_left':
            # Full nut across the slot, measured out to the open exterior.
            motion['nut_load_path']=motion['nut_load_path'].fuse(design.left_nut_tunnel())
        # The washer is a separate component that travels through the larger
        # seat access column, using its actual OD, along with the bolt & bit.
        x,y=h[0]*HOLE_X,h[1]*HOLE_Y
        motion['driver_and_washer_travel']=geom.to_model(
            geom.lcyl(x,y,TAB_FRONT_W+.002,76.,P['washer_od']+.25))
        report[name]=dict(seat_plane_error_mm=min(abs(w-TAB_BACK_W) for w,a in seats),
                          near_axis_seat_area_mm2=area,
                          overlaps_mm3={label:{'core':vol(shape,core),'lcd':vol(shape,lcd)}
                                        for label,shape in {**hw,**motion}.items()})
    return bore_offsets, report
