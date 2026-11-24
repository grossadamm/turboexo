"""Fair the underside of the 42° layered channel without moving its upper skins."""
from __future__ import annotations

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

import cadquery as cq
import numpy as np
import trimesh
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.Geom import Geom_BSplineSurface
from OCP.TColStd import TColStd_Array1OfInteger, TColStd_Array1OfReal
from OCP.TColgp import TColgp_Array2OfPnt
from OCP.gp import gp_Pnt, gp_Vec
from scipy.interpolate import PchipInterpolator, RectBivariateSpline

import layered_channel_wing as layered
import matched_upsweep_wing as matched
import skin_first_wing as skin
import swept_ramp_wing as swept
from twin_spar_wing import heights, intersector, plate_y

D = swept.D
OLD = D / 'layered42_wing'
OUT = D / 'faired42_wing'
HARDWARE = D / 'skin_first_wing'

# Positive aft distance from the car origin and offset from the wheel-side edge.
# The aft spar socket ends at span offset -21.5 and X=-178.2. The spline
# remains below its structural floor, then opens out gently behind the socket.
AFT = np.array([54, 72, 92, 118, 145, 163, 173, 178.2, 185, 193, 203, 212, 220, 222])
START_OFFSET = np.array([-39, -34, -31, -30, -29, -25, -24, -25, -44, -75, -96, -103, -105, -105])
END_OFFSET = np.array([3, 3, 3, 3, 3, 3, 3, 2, 1, -3, -8, -13, -15, -15])
EDGE_Z = np.array([125.9, 127.8, 130.4, 134.1, 138.9, 143.5, 147.0, 149.0, 152.5, 158.8, 169.2, 179.0, 185.25, 186.75])
GEOM_TOL = 1.0e-7


def knot_array(vals, integers=False):
    cls = TColStd_Array1OfInteger if integers else TColStd_Array1OfReal
    arr = cls(1, len(vals))
    for i,v in enumerate(vals, start=1):
        arr.SetValue(i, int(v) if integers else float(v))
    return arr


def face_from_grid(x, y, z):
    spline = RectBivariateSpline(x, y, z, kx=3, ky=3, s=0)
    uk, vk = spline.get_knots()
    uc = [float(np.mean(uk[i+1:i+4])) for i in range(len(uk)-4)]
    vc = [float(np.mean(vk[j+1:j+4])) for j in range(len(vk)-4)]
    poles = TColgp_Array2OfPnt(1, len(uc), 1, len(vc))
    for i, row in enumerate(spline.get_coeffs().reshape(len(uc),len(vc))):
        for j, value in enumerate(row):
            poles.SetValue(i+1,j+1,gp_Pnt(uc[i],vc[j],float(value)))
    u,um=np.unique(uk,return_counts=True)
    v,vm=np.unique(vk,return_counts=True)
    surface = Geom_BSplineSurface(poles,knot_array(u),knot_array(v),
                                 knot_array(um,True),knot_array(vm,True),3,3)
    return BRepBuilderAPI_MakeFace(surface, GEOM_TOL).Face()


def new_lower_tool(side):
    tip = abs(swept.WHEEL_Y[side])
    sign = swept.SIGNS[side]
    source = intersector(swept.read(HARDWARE / f'wing_{side}.step'))
    x = np.arange(-222., -53.99, 1.5)
    o = np.arange(-119., 4.01, 1.5)
    # The original flat underside (with its tangent tail taper) is still the
    # inboard datum. Its existing wheel-edge thinning runs out naturally.
    floor = []
    for xi in x:
        if xi < -219.98:
            zi = heights(source, -219.98, sign * (tip-106))[0]
            floor.append(zi + (-219.98-xi)*.20)
        else:
            floor.append(heights(source, xi, sign * (tip-106))[0])
    floor = np.array(floor)[:,None]
    old_ratio = [
        1. if oi <= -skin.TIP_BLEND_LENGTH else
        (skin.top_z(-133)-heights(source,-133,sign*(tip + min(-0.01,oi)))[0])/skin.DEPTH
        for oi in o
    ]
    original = floor + (np.array([skin.top_z(xi) for xi in x])[:,None] - floor) * (1-np.array(old_ratio)[None,:])
    u = PchipInterpolator(AFT, START_OFFSET)(-x)[:,None]
    v = PchipInterpolator(AFT, END_OFFSET)(-x)[:,None]
    z_edge = PchipInterpolator(AFT, EDGE_Z)(-x)[:,None]
    # Controls spanwise tangency. The broad aft return is one tensor-product
    # spline face, not intersecting lofts with separate start or stop walls.
    t = np.clip((o[None,:] - u)/(v-u),0,1)
    q = np.clip((-x-54.)/34., 0., 1.)[:,None]
    engage = q**3*(10-15*q+6*q*q)
    # A quintic run-in leaves the old underside at the forward cap and
    # prevents the clipping plane itself from becoming a visible step.
    b = t*t*(3-2*t)*engage
    z = (1-b)*original + b*z_edge - .07
    if sign < 0:
        o,z = o[::-1],z[:,::-1]
    face = face_from_grid(x,sign*(tip+o),z)
    tool = cq.Shape.cast(BRepPrimAPI_MakePrism(face,gp_Vec(0,0,-90),True).Shape())
    assert tool.isValid() and len(tool.Solids()) == 1, side
    return tool


def upper_blade(side):
    ribs = [layered.rib(side, f, 42) for f in (0,.25,.5,.75,1)]
    sides = cq.Solid.makeLoft(ribs).Faces()
    caps = [cq.Face.makeNSidedSurface(wire.Edges(),[]) for wire in (ribs[0],ribs[-1])]
    return cq.Solid.makeSolid(cq.Shell.makeShell(sides+caps)).fix()


def generate(side, temporary, output, export_mesh=True):
    sign = swept.SIGNS[side]
    tip = abs(swept.WHEEL_Y[side])
    print(side, 'building the unchanged upper shell', flush=True)
    swept.build(side, temporary, section_shift=matched.shift)
    blank = swept.read(temporary / f'wing_{side}.step')
    tool = new_lower_tool(side)
    print(side, 'backing only the retained skin over cavities', flush=True)
    full = skin.wing_exterior(side, skin.wing_plan(side))
    # Treat the lightening cavities independently from spar engagement. Add
    # stock only where needed to retain the existing 2.4 mm laminate. The
    # tube-shaped socket tools then restore the exact empty nominal pockets.
    backing = full.intersect(tool.translate(cq.Vector(0,0,skin.SHELL_WALL+.10)))
    assert backing.isValid() and backing.Volume() > 0, side
    print(side, 'cutting the continuous fascia', flush=True)
    result = blank.fuse(backing).cut(tool).clean()
    for x in skin.STATIONS.values():
        stop = tip-skin.TIP_STOP+.5
        opening = abs(plate_y(side,x,skin.SPAR_Z))-1.
        result = result.cut(skin.spar_prism(side,x,opening,stop,skin.FIT)).clean()
    assert result.isValid() and len(result.Solids()) == 1, side
    result = result.fuse(upper_blade(side)).clean()
    assert result.isValid() and len(result.Solids()) == 1, side
    path = output / f'wing_{side}.step'
    cq.exporters.export(result,str(path))
    exported = swept.read(path)
    assert exported.isValid() and len(exported.Solids()) == 1, side
    # A valid solid alone is not sufficient. An OCCT cut that fails to apply
    # cleanly can still return a valid solid with the old underbody.
    solid_rays, cutter_rays = intersector(exported), intersector(tool)
    for x in (-125., -150., -175., -185., -195., -205., -215.):
        for offset in (-15., -12., -10.):
            y = sign*(tip+offset)
            want = heights(cutter_rays,x,y)[-1]
            got = heights(solid_rays,x,y)[0]
            assert abs(got-want) < .02, (side,x,offset,got,want)
    volume = exported.Volume(1.e-8)
    print(side, 'valid STEP', volume, flush=True)
    if not export_mesh:
        return
    path = path.with_suffix('.stl')
    exported.exportStl(str(path),tolerance=.018,angularTolerance=.06,relative=False)
    mesh=trimesh.load_mesh(path)
    print(side, 'mesh', len(mesh.faces), mesh.is_watertight, mesh.body_count, mesh.volume, flush=True)
    assert mesh.is_volume and mesh.body_count == 1, side
    assert abs(mesh.volume/volume-1) < .005, side


def main():
    arg = argparse.ArgumentParser()
    arg.add_argument('--side',choices=swept.SIGNS,nargs='+',default=list(swept.SIGNS))
    arg.add_argument('--out',type=Path,default=OUT)
    arg.add_argument('--step-only',action='store_true')
    opts = arg.parse_args()
    opts.out.mkdir(parents=True,exist_ok=True)
    with TemporaryDirectory() as tmp:
        for side in opts.side:
            generate(side,Path(tmp),opts.out,not opts.step_only)


if __name__ == '__main__':
    main()
