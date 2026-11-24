"""Optional integral inboard M6 lugs for the uncut car-left plate.

Uses fitted plate datums, not an assertion of physical fit. The caller owns the
panel geometry and must check full assembly clearance and bolt/nut access.
"""
from pathlib import Path
import json
import cadquery as cq
import numpy as np
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Vec

ROOT = Path(__file__).resolve().parent.parent
PLATE = json.loads((ROOT / 'grid/plate_v2.json').read_text())
R = np.array(PLATE['to_car']['left']['R'])
T = np.array(PLATE['to_car']['left']['t'])
N = R[:, 2]
INNER = T - PLATE['thickness_mm'] * N
HOLES = ('upper', 'B')
LUG_THICKNESS = 6.0
BORE_DIAMETER = 6.8


def top_v(u):
    """Upper intersection of the original plate perimeter in plate coordinates."""
    edges = zip(PLATE['outer'][:-1], PLATE['outer'][1:])
    values = [a[1] + (u-a[0])*(b[1]-a[1])/(b[0]-a[0])
              for a, b in edges if min(a[0],b[0]) <= u <= max(a[0],b[0])
              and abs(b[0]-a[0]) > 1.e-9]
    if not values:
        raise ValueError(f'No plate outline at u={u}')
    return max(values)


def mount(panel):
    """Fuse lugs to panel and return (one solid, verification dict).

    Lug tops extend above the plate outline to engage the user's skin. The
    cutters are applied to lug solids *before* fusion, preserving the skin.
    We reject the result if the panel blocks either resulting bolt bore.
    """
    if isinstance(panel, cq.Workplane):
        panel = panel.val()
    plane = cq.Plane(origin=tuple(INNER), xDir=tuple(R[:,0]), normal=tuple(N))
    # Clip every lug below the real upper skin surface. A downward prism
    # from that face supplies the exact curved upper limit and footprint.
    large = sorted(panel.Faces(), key=lambda face: face.Area(), reverse=True)[:2]
    upper = max(large, key=lambda face: face.Center().z)
    under_skin = cq.Shape.cast(BRepPrimAPI_MakePrism(upper.wrapped, gp_Vec(0, 0, -150)).Shape())
    if not under_skin.isValid() or len(under_skin.Solids()) != 1:
        raise ValueError('Could not construct the upper skin limit')
    lugs = []
    checks = {}
    for name in HOLES:
        u,v = PLATE['holes'][name]['uv']
        width = 18.0
        # Straight sides and bottom: bottom edge is 8 mm below bore center.
        # Extend above the plate top and clip to the real upper skin.
        us = np.linspace(u + width/2, u - width/2, 13)
        points = [(u-width/2,v-8), (u+width/2,v-8)]
        points += [(float(x), float(top_v(x)+12)) for x in us]
        lug = cq.Workplane(plane).polyline(points).close().extrude(-LUG_THICKNESS).val().intersect(under_skin)
        center = INNER + R[:,0]*u + R[:,1]*v
        cutter = cq.Solid.makeCylinder(BORE_DIAMETER/2, LUG_THICKNESS+0.2,
                                       cq.Vector(*(center+N*0.1)), cq.Vector(*(-N)))
        # A blocked passage means it is unsafe to silently cut the panel skin.
        blocked = panel.intersect(cutter).Volume()
        checks[name] = {'inner_face_xyz_mm': center.tolist(),
                        'bore_diameter_mm': BORE_DIAMETER,
                        'panel_bore_obstruction_mm3': blocked}
        if blocked > 0.01:
            raise ValueError(f'{name} lug bore intersects panel ({blocked:.3f} mm³)')
        lugs.append(lug.cut(cutter))
    result = panel.fuse(*lugs).clean()
    if not result.isValid() or len(result.Solids()) != 1:
        raise ValueError('Lugs did not fuse to panel as one valid solid')
    checks['single_valid_solid'] = True
    return result, checks
