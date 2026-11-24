"""OEM installation, bench extraction and sightline envelopes."""
import json
import numpy as np
import cadquery as cq
from scipy.spatial import ConvexHull
from params import (P, REF, HOLE_X, HOLE_Y, BODY_HALF_X, BODY_HALF_Y, TAB_BACK_W,
                    TAB_FRONT_W, TAB_END_X, TAB_HALF_H, ACTIVE_CX, ACTIVE_H,
                    ACTIVE_W, OEM_FRONT_CENTER, OEM_TO_LOCAL, local_to_model)
from geom import to_model, lbox

# Display-local waypoints (up, toward viewer) in millimeters.
SERVICE_PATH = ((0., 0.), (10., 20.), (10., 250.))

def oem_box_to_local(b):
    lo = (np.array(b[:3]) - OEM_FRONT_CENTER) @ OEM_TO_LOCAL.T
    hi = (np.array(b[3:]) - OEM_FRONT_CENTER) @ OEM_TO_LOCAL.T
    return np.minimum(lo, hi), np.maximum(lo, hi)


def v(p):
    return cq.Vector(*p)


def component_boxes():
    components = json.loads((REF / 'vendor/vendor_extract.json').read_text())['components']
    return [oem_box_to_local(c['bbox_oem']) for c in components]


def display_bounds():
    """Conservative body, four lug strips and component bounds in local mm."""
    b, h = BODY_HALF_X, BODY_HALF_Y
    yield np.array([-b, -h, TAB_BACK_W]), np.array([b, h, 0.])
    for side in (-1, 1):
        y = side * HOLE_Y
        yield (np.array([-TAB_END_X, y-TAB_HALF_H, TAB_BACK_W]),
               np.array([TAB_END_X, y+TAB_HALF_H, TAB_FRONT_W]))
    # Five-mm x slices bound all OEM PCB solids without fusing 1,339 boxes.
    components = np.asarray(component_boxes())
    for x in range(-75, 85, 5):
        subset = components[(components[:, 1, 0] > x) & (components[:, 0, 0] < x+5)]
        if len(subset):
            lo, hi = subset[:, 0].min(axis=0), subset[:, 1].max(axis=0)
            lo[0], hi[0] = max(lo[0], x), min(hi[0], x+5)
            yield lo, hi


def sweep_box(lo, hi, a, b):
    yz = np.array([[y+dy, w+dw] for y in (lo[1], hi[1]) for w in (lo[2], hi[2])
                   for dy, dw in (a,b)])
    outline = yz[ConvexHull(yz).vertices].tolist()
    return to_model(cq.Workplane('YZ', origin=(lo[0],0,0)).polyline(outline)
                    .close().extrude(hi[0]-lo[0]).val())


def display_sweep(clearance=0., body_clearance=None):
    for i, (lo, hi) in enumerate(display_bounds()):
        extra = body_clearance if i == 0 and body_clearance is not None else clearance
        for a, b in zip(SERVICE_PATH, SERVICE_PATH[1:]):
            yield sweep_box(lo-extra, hi+extra, a, b)


def left_nut_tunnel(extra=0.):
    # Side load via a long open slot. The original trap and seat stay intact.
    w = TAB_BACK_W - P['pad_front_web']
    y = -HOLE_Y
    half = P['nut_af_nom']/2 + extra
    return to_model(lbox(-137., -HOLE_X, y-half, y+half,
                         w-P['nut_t_nom']-extra, w+extra))


def viewing_keepouts():
    buffer = 2.65
    b, h = ACTIVE_W/2+buffer, ACTIVE_H/2+buffer
    corners = local_to_model([[ACTIVE_CX+x,y,0.] for x,y in
                              [(-b,-h),(b,-h),(b,h),(-b,h)]])
    yield to_model(lbox(ACTIVE_CX-b, ACTIVE_CX+b, -h, h, 0., 400.))
    for eye in json.loads((REF / 'viewpoints.json').read_text())['camera_centers'].values():
        end = .002*corners + .998*np.asarray(eye)
        wires = [cq.Wire.makePolygon([v(p) for p in (*r,r[0])]) for r in (corners,end)]
        yield cq.Solid.makeLoft(wires, ruled=True)
