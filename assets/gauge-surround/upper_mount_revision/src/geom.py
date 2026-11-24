"""Hood-profile and OEM LCD construction primitives in millimeters."""
import json
import numpy as np
import cadquery as cq
from OCP.gp import gp_Trsf, gp_Ax3, gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform

from params import (REF, P, R, C, local_to_model, HOLE_X, HOLE_Y, TAB_BACK_W,
                    TAB_FRONT_W, BODY_HALF_X, BODY_HALF_Y, cheek_vertices_new)

def trsf_local():
    t = gp_Trsf()
    t.SetTransformation(gp_Ax3(gp_Pnt(*C), gp_Dir(*R[:, 2]), gp_Dir(*R[:, 0])), gp_Ax3())
    return t


def to_model(shape):
    """rigid display-local -> model transform (exact gp_Trsf, det +1)."""
    return cq.Shape.cast(BRepBuilderAPI_Transform(shape.wrapped, trsf_local(), True).Shape())


def lbox(x0, x1, y0, y1, w0, w1):
    """axis-aligned box in display-local frame (returned in local)."""
    return cq.Solid.makeBox(x1 - x0, y1 - y0, w1 - w0, cq.Vector(x0, y0, w0))


def lcyl(x, y, w0, w1, d):
    return cq.Solid.makeCylinder(d / 2, w1 - w0, cq.Vector(x, y, w0), cq.Vector(0, 0, 1))


def lhex(x, y, w0, w1, af):
    circ = af / np.cos(np.pi / 6)
    return cq.Workplane('XY', origin=(x, y, w0)).polygon(6, circ).extrude(w1 - w0).val()


def mbox(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def xz_of(y, w, x_local):
    p = local_to_model([x_local, y, w])[0]
    return np.array([p[0], p[2]])


def line_int(p1, d1, p2, d2):
    A = np.array([d1, -d2]).T
    t = np.linalg.solve(A, p2 - p1)
    return p1 + t[0] * d1


def wall_profile(x_local):
    """Returns (outer, hole) XZ polygons for a side wall at local x = x_local."""
    ch, _ = cheek_vertices_new()
    rear_top = np.array([max(ch['top_outboard'][0], 0.0), 6.0])      # extended above hood, clipped later
    rear_bot = np.array([max(ch['bottom_outboard'][0], 0.0), ch['bottom_outboard'][2]])
    bot_in = np.array([ch['bottom_inboard'][0], ch['bottom_inboard'][2]])
    wf, wb, ymin = P['rail_w_front'], P['rail_w_back'], P['rail_y_min']
    f0, f1 = xz_of(0, wf, x_local), xz_of(-10, wf, x_local)          # rail front line
    dF = f1 - f0
    cheek_hit = line_int(rear_bot, bot_in - rear_bot, f0, dF)
    F_bot = xz_of(ymin, wf, x_local)
    A = xz_of(ymin, wb, x_local)
    S2 = np.array([188.0, 6.0])
    # strut lower edge A->S_hood(188,0); extend above hood
    dS = np.array([188.0, 0.0]) - A
    S2 = A + dS * (6.0 - A[1]) / dS[1]
    outer = [rear_top, rear_bot, cheek_hit, F_bot, A, S2]
    # inner opening: between rail back line, strut (offset 14 mm), hood underside -9
    n = np.array([-dS[1], dS[0]]); n /= np.linalg.norm(n)
    if n[0] > 0: n = -n                                          # offset toward rail (rearward)
    sp = A + n * 14.0
    b0, b1 = xz_of(0, wb, x_local), xz_of(-10, wb, x_local)
    dB = b1 - b0
    ztop = -3.0 - 7.0
    H1 = line_int(b0, dB, np.array([0, ztop]), np.array([1.0, 0]))
    H2 = line_int(b0, dB, sp, dS)
    H3 = line_int(sp, dS, np.array([0, ztop]), np.array([1.0, 0]))
    # keep the rail band at least 14 mm deep behind lower pads: move H2 up if needed
    return [tuple(map(float, p)) for p in outer], [tuple(map(float, p)) for p in (H1, H2, H3)]


def wall_solid(yr, x_local, r_out=5.0, r_in=6.0):
    outer, hole = wall_profile(x_local)
    sk = (cq.Sketch().polygon(outer + [outer[0]]).polygon(hole + [hole[0]], mode='s')
          .vertices().fillet(r_out))
    wp = cq.Workplane('XZ').placeSketch(sk).extrude(-(yr[1] - yr[0]))   # XZ normal is -Y; negative -> +Y
    s = wp.val()
    bb = s.BoundingBox()
    return s.translate(cq.Vector(0, yr[0] - bb.ymin, 0))


def pad_local(sx, sy):
    """Mount pad (local frame) incl. bore, hex pocket & side-loading slot cuts returned separately."""
    a_in = HOLE_X - P['pad_inboard']
    a_end = 94.5
    b0, b1 = HOLE_Y - P['pad_b_in'], HOLE_Y + P['pad_b_out']
    w1 = TAB_BACK_W; w0 = w1 - P['pad_depth']
    xs = sorted([sx * a_in, sx * a_end]); ys = sorted([sy * b0, sy * b1])
    pad = lbox(xs[0], xs[1], ys[0], ys[1], w0, w1)
    return clear_pad(pad, sx, sy)


def upper_pad_local(sx):
    """Rounded upper ear with a tangential ramp into the roof at the rail."""
    y = HOLE_Y
    r = 5.35
    x_end = 94.5
    front = TAB_BACK_W
    back = front - P['pad_depth']

    def pt(x, y):
        return cq.Vector(sx*x, y, back)

    lower = pt(HOLE_X, y-r)
    nose = pt(HOLE_X-r, y)
    upper = pt(HOLE_X, y+r)
    root_top = pt(x_end, y+8.9)
    root_bottom = pt(x_end, y-r)
    profile = cq.Wire.assembleEdges([
        cq.Edge.makeThreePointArc(lower, nose, upper),
        cq.Edge.makeBezier([upper, pt(HOLE_X+3.,y+r),
                            pt(x_end-2.,y+8.0), root_top]),
        cq.Edge.makeLine(root_top, root_bottom),
        cq.Edge.makeLine(root_bottom, lower),
    ])
    pad = cq.Solid.extrudeLinear(profile, [], cq.Vector(0,0,front-back))
    # Break the free rim at the noses and underside. The top rim keeps its
    # full section where it blends into the roof.
    rim = [edge for edge in pad.Edges()
           if abs(edge.Center().z-front)<1e-6 and
           (edge.geomType()=='CIRCLE' or abs(edge.Center().y-(y-r))<1e-6)]
    pad = pad.fillet(.65, rim)
    return clear_pad(pad, sx, 1, b_out=9.)


def clear_pad(pad, sx, sy, b_out=None):
    """Relieve the OEM display body and flex where they approach a pad."""
    a_in = HOLE_X - P['pad_inboard']
    b0, b1 = HOLE_Y - P['pad_b_in'], HOLE_Y + (P['pad_b_out'] if b_out is None else b_out)
    ys = sorted([sy * b0, sy * b1])
    w1 = TAB_BACK_W
    w0 = w1 - P['pad_depth']
    # Recess where the pad overlaps the body footprint.
    a_rec = BODY_HALF_X + P['flex_overhang_x'] + P['clr_body']
    xr = sorted([sx * (a_in - 1), sx * a_rec])
    pad = pad.cut(lbox(xr[0], xr[1], ys[0] - 1, ys[1] + 1, w1 - P['pad_recess_over_body'], w1 + 1))
    # corner notch keeping the vendor flex (solid 3, local x<=82.45, y<=44.66) rear sweep clear by notch_clr
    nx = 82.45 + P['notch_clr']; ny = 44.66 + P['notch_clr']
    xn = sorted([sx * (a_in - 1), sx * nx]); yn = sorted([sy * (b0 - 1), sy * ny])
    pad = pad.cut(lbox(xn[0], xn[1], yn[0], yn[1], w0 - 1, w1 + 1))
    return pad


def pad_cuts_local(sx, sy):
    hx, hy = sx * HOLE_X, sy * HOLE_Y
    w1 = TAB_BACK_W
    wn0 = w1 - P['pad_front_web'] - P['nut_pocket_depth']; wn1 = w1 - P['pad_front_web']
    bore = lcyl(hx, hy, w1 - P['pad_depth'] - P['bore_tip_relief'], w1 + 0.5, P['m3_bore'])
    hexp = lhex(hx, hy, wn0, wn1, P['nut_af_pocket'])
    xs = sorted([hx, sx * 101.0])
    slot = lbox(xs[0], xs[1], hy - P['nut_af_pocket'] / 2, hy + P['nut_af_pocket'] / 2, wn0, wn1)
    # front access: washer/head + hex key clearance column, toward viewer
    head = lcyl(hx, hy, TAB_FRONT_W, 60.0, P['washer_od'] + 2.0)
    return [bore, hexp, slot, head]


def body_keepout_local(clr):
    return lbox(-BODY_HALF_X - clr, BODY_HALF_X + clr, -BODY_HALF_Y - clr, BODY_HALF_Y + clr, TAB_BACK_W - clr, clr)


def usb_ports_local():
    import json
    con = json.load(open(REF / 'vendor/vendor_connectors.json'))
    out = {}
    for c in con:
        k = c['name'].split('| ')[1].split('^')[0]
        if k in ('USB', 'USB-PROG'):
            out[k] = (np.array(c['bbox_local'][0]), np.array(c['bbox_local'][1]))
    return out


def usb_envelope(ext=0.0, L=None):
    """Straight plug envelope per port: overmold allowance centred on receptacle, from receptacle face along +y."""
    L = P['usb_plug_len'] if L is None else L
    env = []
    for k, (lo, hi) in usb_ports_local().items():
        cx, cw = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
        hw, ht = P['usb_overmold_w'] / 2 + ext, P['usb_overmold_t'] / 2 + ext
        env.append(to_model(lbox(cx - hw, cx + hw, hi[1], hi[1] + L, cw - ht, cw + ht)))
    return env


def usb_aperture():
    slab = mbox(-50, 350, -100, 300, -3, 0)
    u = None
    for e in usb_envelope(P['usb_ap_clr']):
        i = e.intersect(slab); u = i if u is None else u.fuse(i)
    b = u.BoundingBox()
    r = lambda v, up: (np.ceil(v * 10) if up else np.floor(v * 10)) / 10
    return r(b.xmin, False), r(b.xmax, True), r(b.ymin, False), r(b.ymax, True)
