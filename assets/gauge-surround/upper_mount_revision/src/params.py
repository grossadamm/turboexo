"""Design parameters + display pose math for the gauge surround (all units mm).
Frame: hood CAD frame (origin hood rear-right top corner, +X forward, +Y car-left, +Z hood normal).
Display local frame: x = viewer right, y = up, z(w) = toward viewer, origin = front glass body centre.
"""
import json, numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REF = Path(__file__).resolve().parents[1] / 'inputs'
DES = Path(__file__).resolve().parents[1]
BUILD = DES / 'build'
DELIV = DES / 'deliverables'

_pose = json.load(open(REF / 'display_pose.json'))['new']
C = np.array(_pose['center'], float)
_Rraw = np.array(_pose['local_axes_columns_x_right_y_up_z'], float)  # rows listed, columns = axes
_U, _S, _Vt = np.linalg.svd(_Rraw)
R = _U @ _Vt
if np.linalg.det(R) < 0:
    raise ValueError('pose matrix not right-handed')
R_ORTHO_DEV = float(np.abs(R - _Rraw).max())

# ---- OEM (vendor STEP) datums -------------------------------------------------
OEM_FRONT_CENTER = np.array([61.4796478868, 92.7154484110, 146.7638183366])
OEM_TO_LOCAL = np.diag([-1.0, -1.0, 1.0])       # viewer-right=-OEMX, up=-OEMY, toward viewer=+OEMZ
R_OEM = R @ OEM_TO_LOCAL                         # OEM -> model rotation (det +1)
OEM_HOLES = [(x, y) for x in (-25.3703521132, 148.3296478868) for y in (43.5154484110, 141.9154484110)]
OEM_TAB_BACK_Z = 142.5638183366
OEM_TAB_FRONT_Z = 143.1638183366

def oem_to_model(p):
    p = np.atleast_2d(np.asarray(p, float))
    return (p - OEM_FRONT_CENTER) @ R_OEM.T + C

def local_to_model(p):
    p = np.atleast_2d(np.asarray(p, float))
    return p @ R.T + C

def model_to_local(p):
    p = np.atleast_2d(np.asarray(p, float))
    return (p - C) @ R

# ---- vendor-derived display nominal (local) ------------------------------------
BODY_W, BODY_H = 164.8, 109.3           # drawing nominal; CAD bbox 164.7 x 109.2
BODY_HALF_X = (143.82965 - -20.87035) / 2   # 82.35 CAD
BODY_HALF_Y = (147.31545 - 38.11545) / 2    # 54.60 CAD
ACTIVE_W, ACTIVE_H, ACTIVE_CX = 150.72, 94.2, -1.65
HOLE_X, HOLE_Y = 86.85, 49.2            # +-, from CAD (pattern 173.7 x 98.4)
TAB_FRONT_W = -(146.7638183366 - OEM_TAB_FRONT_Z)   # -3.6
TAB_BACK_W = -(146.7638183366 - OEM_TAB_BACK_Z)     # -4.2
TAB_END_X = 90.85                       # hole + R4 lug end (overall 181.7)
TAB_HALF_H = 4.0                        # 8.0 lug width (drawing)
MODULE_DEPTH = 146.7638183366 - 131.3276223262       # 15.44 (CAD)

# ---- design allowances (explicit design choices) --------------------------------
P = dict(
    wall_t=3.0, hood_t=3.0,
    clr_body=1.0,            # printed part to LCD body (except tab contact)
    clr_tab_lateral=2.0,     # side wall inner face to module outline incl. tabs
    clr_active_ray=2.0,      # ray / view clearance target
    clr_component=1.0,       # to vendor PCB/component bboxes
    pad_recess_over_body=1.5,
    flex_overhang_x=0.10,    # vendor flex (solid 3) protrudes 0.10 beyond body edge at upper-right; recess zone covers it
# pad face set back behind LCD back plate where pad overlaps body footprint
    notch_clr=0.6,           # pad inboard corner notch vs rear sweep of vendor flex bbox (keeps >=2 mm hex wall)
    m3_bore=3.4, nut_af_nom=5.5, nut_t_nom=2.4, nut_af_pocket=5.75, nut_pocket_depth=2.8,
    pad_front_web=3.0, pad_back_web=2.5,
    pad_inboard=5.4, pad_b_in=4.9, pad_b_out=5.5,
    bore_tip_relief=0.6,
    head_d=5.5, head_h=3.0, washer_od=6.0, washer_t=0.5,   # ISO 4762 M3, DIN 433 M3 washer
    display_bolt_len=8.0,
    rail_y_min=-60.0, rail_w_front=2.0, rail_w_back=-16.0,
    # USB Type-C modeled plug envelope and aperture relief.
    usb_overmold_w=12.35, usb_overmold_t=6.5, usb_plug_len=20.0, usb_ap_clr=1.0,
)
P['pad_depth'] = P['pad_front_web'] + P['nut_pocket_depth'] + P['pad_back_web']

HOOD = [(0, 0), (279.48, 0), (279.48, 174.12), (0, 171.95)]
def hood_left_y(x):
    return 171.95 + (174.12 - 171.95) * x / 279.48

def hole_local(sx, sy, w=TAB_BACK_W):
    return np.array([sx * HOLE_X, sy * HOLE_Y, w])

HOLES = [(sx, sy) for sx in (1, -1) for sy in (1, -1)]
HOLE_NAMES = {(1, 1): 'top_right', (1, -1): 'bottom_right', (-1, 1): 'top_left', (-1, -1): 'bottom_left'}

def module_y_extent():
    """Model-Y extent of module outline (body + lugs) over front..back of lug/body."""
    pts = []
    for sx in (1, -1):
        for sy in (1, -1):
            for w in (0.0, TAB_BACK_W):
                pts.append([sx * TAB_END_X, sy * (HOLE_Y + TAB_HALF_H), w])
                pts.append([sx * BODY_HALF_X, sy * BODY_HALF_Y, w])
    m = local_to_model(pts)
    return float(m[:, 1].min()), float(m[:, 1].max())

YMIN_MOD, YMAX_MOD = module_y_extent()
WALL_R_IN = round(YMIN_MOD - P['clr_tab_lateral'] - 0.005, 2)   # right wall inner face Y
WALL_L_IN = round(YMAX_MOD + P['clr_tab_lateral'] + 0.005, 2)
WALL_R = (WALL_R_IN - P['wall_t'], WALL_R_IN)
WALL_L = (WALL_L_IN, WALL_L_IN + P['wall_t'])

# new-registration cheek vertices (old model -> world -> new model)
def cheek_vertices_new():
    g = json.load(open(REF / 'mockup_geometry.json'))['cheek']['vertices_model_mm']
    o = json.load(open(REF / 'old_scan_transform.json')); n = json.load(open(REF / 'updated_scan_transform.json'))
    Ro, Oo, So = np.array(o['rotation_rows_world_to_model']), np.array(o['origin_world']), o['mm_per_world_unit']
    Rn, On, Sn = np.array(n['rotation_rows_world_to_model']), np.array(n['origin_world']), n['mm_per_world_unit']
    out = {}
    for k, p in g.items():
        world = (np.array(p) / So) @ Ro + Oo
        out[k.split(' ')[0]] = ((world - On) @ Rn.T * Sn).tolist()
    return out, g
