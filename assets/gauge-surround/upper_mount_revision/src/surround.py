"""Build the one-piece surround in hood XYZ, in millimeters.

The shade and OEM lugs derive from the measured hood and corrected LCD frame.
Each vehicle flange and gusset derives from its released slot frame. Neither
support uses an imported solid or the earlier bracket geometry.
"""
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path

import cadquery as cq
import numpy as np

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parent
from geom import (body_keepout_local, lcyl, mbox, pad_cuts_local, pad_local,
                  to_model, upper_pad_local, wall_profile, wall_solid)
from service import display_sweep, left_nut_tunnel, viewing_keepouts
from params import C, HOLES, HOLE_X, HOLE_Y, P, TAB_FRONT_W, WALL_L, WALL_R, hood_left_y

SLOT_DATUMS = json.loads((OUT / "inputs/vehicle_slots.json").read_text())["sides"]
PAD_DEPTH = 6.0
# Increase the polymer slot modestly around the same measured steel axes.
PRINTED_SLOT = {"right": (8.4, 5.5), "left": (8.4, 6.6)}
PAD_RADIUS = {"right": 8.0, "left": 8.0}
# h is approximately hood-up, n is toward the driver; u is car-left.
# UV profile fans toward the wall. Normal profile increases depth before
# turning back into the existing rail. Left return starts above the green lip.
PLAN_PROFILE = {
    "right": [(-7, 3.2), (7, 2.8), (17, 10), (24, 19), (26, 35),
              (22, 55), (17, 56), (8, 34), (-2, 18)],
    "left": [(-5, 2.7), (7.5, 2.7), (16, 9), (20, 18), (19, 33),
             (10, 55), (4, 56), (2, 35), (3, 22), (-2, 14)],
}
DEPTH_PROFILE = {
    "right": [(0.9, 3), (5.85, 3), (6.8, 7), (13.3, 16), (15.0, 48),
              (10, 56), (4, 53), (-6, 31), (-4, 23), (0.3, 14)],
    "left": [(1.0, 3), (5.85, 3), (7.7, 7.5), (10.5, 15), (8.0, 30),
             (6.3, 53), (1, 56), (-6, 49), (-12, 30), (-10.0, 24),
             (-4.5, 21), (2.5, 17), (2.5, 11), (1.0, 7.5)],
}
PROFILE_RADIUS = 1.8
# Hood XYZ witnesses on the concave web-to-wall joints. A distance check
# guards against selecting an unrelated edge after changing a profile.
ROOT_BLENDS = {
    "right rail transition": (137.23397237487853, -0.5958532438459461, -89.71106499720067),
    "left outboard rail transition": (141.82580864930108, 188.25, -79.63854541145925),
    "left inboard rail transition": (141.77711208559555, 185.25, -79.6337581605235),
}
ROOT_RADIUS = 2.2
# Stock relief based on a compact tool close to the pad, and on the head and
# short shank approach. Swept laterally over the center travel of a 4 mm pin.
TOOL_STEPS = {"right": [(12, 35)], "left": [(10, 12), (6, 13)]}


def vec(point):
    return cq.Vector(*point)


@dataclass
class Mount:
    side: str
    center: np.ndarray
    n: np.ndarray
    u: np.ndarray
    up: np.ndarray
    major: np.ndarray
    length: float
    width: float

    def at(self, u=0, h=0, n=0):
        return self.center + u*self.u + h*self.up + n*self.n

    def axial_plane(self, depth=0):
        return cq.Plane(vec(self.at(n=depth)), vec(self.major), vec(self.n))

    def section_plane(self, h):
        return cq.Plane(vec(self.at(h=h)), vec(self.u), vec(self.up))

    def capsule(self, length, width, near, far):
        wp = cq.Workplane(self.axial_plane(near))
        if abs(length-width) < 1e-7:
            return wp.circle(width/2).extrude(far-near).val()
        return wp.slot2D(length, width).extrude(far-near).val()

    def slot(self, allowance=0, near=-0.25, far=PAD_DEPTH+0.25):
        return self.capsule(self.length+2*allowance, self.width+2*allowance, near, far)

    def access(self, od, near, far, pin=4.0):
        return self.capsule(self.length-pin+od, self.width-pin+od, near, far)


def mount_frame(side):
    data = SLOT_DATUMS[side]
    n = np.array(data["driver_axis_xyz"])
    u = np.array([0., 1., 0.])-n[1]*n
    u /= np.linalg.norm(u)
    return Mount(side, np.array(data["pad_vehicle_face_entry_mm"]), n, u,
                 -np.cross(n, u), np.array(data["slot_major_axis_xyz"]), *PRINTED_SLOT[side])


def profile_prism(plane, points, depth):
    sketch = cq.Sketch().polygon(points + [points[0]]).vertices().fillet(PROFILE_RADIUS)
    return cq.Workplane(plane).placeSketch(sketch).extrude(depth).val()


def web(m):
    plan = profile_prism(cq.Plane(vec(m.at(n=19)), vec(m.u), vec(-m.n)),
                         PLAN_PROFILE[m.side], 36)
    depth = profile_prism(cq.Plane(vec(m.at(u=-20)), vec(m.n), vec(m.u)),
                          DEPTH_PROFILE[m.side], 55)
    return plan.intersect(depth).clean()


@lru_cache
def service_keepouts():
    # Both translation legs model the LCD body, lugs and PCB as swept bounds.
    return tuple(display_sweep(clearance=.2, body_clearance=1.0))


def trim_web(solid, m):
    for cut in service_keepouts():
        solid = solid.cut(cut)
    if m.side == "left":
        driver = to_model(lcyl(-HOLE_X, -HOLE_Y, TAB_FRONT_W, 85., 6.8))
        solid = solid.cut(left_nut_tunnel(.45), driver, *viewing_keepouts())
    return solid.clean()


def support(m):
    # Identical axial thickness at both flat washer faces. Shift the reinforcing
    # section driverward above the left washer instead of pocketing the root.
    flange = cq.Workplane(m.axial_plane()).circle(PAD_RADIUS[m.side]).extrude(PAD_DEPTH).val()
    raw = flange.fuse(web(m)).clean()
    for od, reach in TOOL_STEPS[m.side]:
        raw = raw.cut(m.access(od, PAD_DEPTH, PAD_DEPTH+reach))
    return trim_web(raw, m)


def left_wall():
    """Lay out the lower rail behind the exposed steel lip in hood XZ."""
    x_lcd = C[1] - sum(WALL_L)/2
    upper, void = wall_profile(x_lcd)
    # Preserve the cheek and triangular roof brace. Below the opening, the
    # rail bends back behind the green tab, then turns forward above its lip.
    outline = upper[:3] + [(122.0,-92.0), (125.5,-108.5), (131.0,-106.0),
                            (131.3,-95.0), (146.5,-85.0)] + upper[-1:]
    outside = cq.Sketch().polygon(outline+[outline[0]]).vertices().fillet(3.0)
    inside = cq.Sketch().polygon(void+[void[0]]).vertices().fillet(5.0)
    wp = cq.Workplane('XZ', origin=(0,WALL_L[0],0))
    width = -(WALL_L[1]-WALL_L[0])
    wall = wp.placeSketch(outside).extrude(width).val()
    return wall.cut(wp.placeSketch(inside).extrude(width).val()).clean()


def lcd_seat(sx, sy):
    seat = upper_pad_local(sx) if sy > 0 else pad_local(sx, sy)
    if (sx,sy) == (-1,-1):
        # Keep the mount face and bore center. The rear saddle meets the rail
        # behind the green tab, while its front wing ends beside the lug.
        profile = [(-90.15,0),(-70.,0),(-70.,-16.),(-97.,-16.),
                   (-97.,-10.7),(-90.15,-7.15)]
        clip = (cq.Workplane('XZ', origin=(0,-40,0)).polyline(profile)
                .close().extrude(24).val())
        seat = seat.intersect(clip).clean()
    return to_model(seat)


def core():
    # Straight full-length edges retain the width needed around both sidewalls.
    roof_outline = [(0,WALL_R[0]), (279.48,WALL_R[0]),
                    (279.48,WALL_L[1]), (0,WALL_L[1])]
    roof = cq.Workplane('XY').polyline(roof_outline).close().extrude(-P['hood_t']).val()
    right = wall_solid(WALL_R, C[1]-sum(WALL_R)/2)
    body = roof.fuse(right,left_wall(),*(lcd_seat(*h) for h in HOLES)).clean()
    cuts = [to_model(c) for h in HOLES for c in pad_cuts_local(*h)]
    return body.cut(*cuts,to_model(body_keepout_local(P['clr_body']))).intersect(
        mbox(-10,279.48,-20,210,-200,0)).clean()


def make():
    base = core()
    mounts = {side: mount_frame(side) for side in SLOT_DATUMS}
    supports = {side: support(m) for side, m in mounts.items()}
    united = base.fuse(*supports.values()).clean()
    if len(united.Solids()) != 1:
        raise ValueError("Vehicle webs must have a positive-volume union with the rails")
    return base, mounts, supports, united


def build():
    base, mounts, supports, part = make()
    for name, point in ROOT_BLENDS.items():
        witness = vec(point)
        edge = min(part.Edges(), key=lambda e: (e.positionAt(.5)-witness).Length)
        if (edge.positionAt(.5)-witness).Length > .02:
            raise ValueError(f"Update the blend witness for {name}")
        part = part.fillet(ROOT_RADIUS,[edge]).clean()
    for m in mounts.values():
        part = part.cut(m.slot()).clean()
    if not part.isValid() or len(part.Solids()) != 1:
        raise ValueError("Slots must leave one valid BRep")
    return base, mounts, supports, part


if __name__ == "__main__":
    _, _, _, part = build()
    cq.exporters.export(part, str(OUT / "surround.step"))
    cq.exporters.export(part, str(OUT / "surround.stl"), tolerance=.032, angularTolerance=.07)
    print(f"Fresh surround · {part.Volume():,.1f} mm³")
