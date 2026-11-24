"""An integral cantilevered upper blade following the matched outboard channel."""
from math import sqrt, radians, tan
import cadquery as cq
from swept_ramp_wing import D, SIGNS, RUN, RADIUS, START, WHEEL_Y, read
from upsweep36_wing import shelf

OUT = D/'layered_channel_wing'
BASE = D/'matched_upsweep_wing'


def rib(side, fraction, exit_deg=None):
    span = -1.2 + 47*fraction
    nose = -145 - 16*fraction**2
    tail = -218 + 4*fraction**2
    thick = 4.0 - 1.3*fraction
    gap = 10.0
    def p(t, height):
        x = nose + (tail-nose)*t
        crest = abs(WHEEL_Y[side])-58+sqrt(RADIUS**2-RUN**2)-sqrt(RADIUS**2-(START-x)**2)
        z = shelf(x)+gap+height
        if exit_deg is not None and t > .5:
            # Add a tangent-continuous opening over the rear half of this rib.
            run = (nose-tail)/2
            u = (t-.5)*2
            floor_slope = (shelf(tail-.001)-shelf(tail+.001))/.002
            z += .5*(tan(radians(exit_deg))-floor_slope)*run*u*u
        return cq.Vector(x, SIGNS[side]*(crest+span), z)
    # Both skins follow the channel. The rounded nose and tapered rear are
    # drawn in the same fore/aft section at each span station.
    def spline(ts,hs, exit_tangent=False):
        points = [p(t,h) for t,h in zip(ts,hs)]
        if exit_tangent:
            dx = .001
            dcrest_dx = (START-tail)/sqrt(RADIUS**2-(START-tail)**2)
            tangent = cq.Vector(dx, -SIGNS[side]*dcrest_dx*dx, -tan(radians(exit_deg))*dx)
            # The underside runs from the rear edge toward the nose.
            return cq.Edge.makeSpline(points,tangents=[tangent.normalized()]+[None]*(len(points)-1))
        return cq.Edge.makeSpline(points)
    ts = [.026,.12,.30,.50,.72,.90,1.]
    upper = spline(ts,[thick*.9,thick,thick,thick*.92,thick*.77,thick*.55,thick*.38])
    lower = spline(ts[::-1],[.12,0,0,0,0,0,thick*.10],exit_deg is not None)
    nose_edge = cq.Edge.makeBezier([p(.026,thick*.10),p(-.01,thick*.15),
                                    p(-.01,thick*.85),p(.026,thick*.90)])
    return cq.Wire.assembleEdges([upper,cq.Edge.makeLine(upper.endPoint(),lower.startPoint()),lower,nose_edge])


def build(side, output=OUT, exit_deg=None):
    wing = read(BASE/f'wing_{side}.step')
    ribs = [rib(side,f,exit_deg) for f in (0,.25,.5,.75,1)]
    sides = cq.Solid.makeLoft(ribs).Faces()
    caps = [cq.Face.makeNSidedSurface(wire.Edges(),[]) for wire in (ribs[0],ribs[-1])]
    blade = cq.Solid.makeSolid(cq.Shell.makeShell(sides+caps)).fix()
    assert blade.isValid() and blade.Volume()>0
    result = wing.fuse(blade).clean()
    assert result.isValid() and len(result.Solids())==1
    path = output/f'wing_{side}.step'
    cq.exporters.export(result,str(path))
    check = read(path)
    assert check.isValid() and len(check.Solids())==1
    check.exportStl(str(path.with_suffix('.stl')),tolerance=.018,angularTolerance=.06)


if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    for side in SIGNS:
        build(side)
