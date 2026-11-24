"""Raised outboard trailing panel and integrated swept vane in the car frame."""
from math import radians, sin, sqrt

import cadquery as cq
from skin_first_wing import D, FOLD_X, RAMP_X, SIGNS, TAIL_X, WHEEL_Y, read, top_z, wing_plan

OUT = D / 'swept_ramp_wing'
BASE = D / 'skin_first_wing'
START = -36.0
CREST_HEIGHT = 40.0
TIP_RISE = 15.0
EXIT_INSET = 58.0
EXIT_TANGENT = radians(16)
RUN = START - TAIL_X
RADIUS = RUN / sin(EXIT_TANGENT)


def profile(side, x, shelf_adjust=None, section_shift=None):
    tip = abs(WHEEL_Y[side])
    distance = START - x
    t = distance / RUN
    blend = t*t*(3 - 2*t)
    crest = tip - EXIT_INSET + sqrt(RADIUS**2-RUN**2) - sqrt(RADIUS**2-distance**2)
    pedestal = top_z(x) - 0.08
    inboard_width = 22.0 + 22.0*blend

    def p(y, rise):
        z = pedestal + rise*blend
        if shelf_adjust is not None and rise > 0:
            w = max(0., min(1., (y-crest)/18.))
            z += shelf_adjust(x)*w*w*(3-2*w)
        if section_shift is not None:
            z += section_shift(x, y, crest, inboard_width, rise, blend)
        return cq.Vector(x, SIGNS[side]*y, z)

    def bezier(*points):
        return cq.Edge.makeBezier([p(y,h) for y,h in points])

    foot = crest - inboard_width
    # The inboard face rolls out of the flat skin and leans toward the tire.
    crown = CREST_HEIGHT + 0.08
    shelf = TIP_RISE + 0.08
    edges = [
        bezier((foot, 0), (foot+12, 0), (crest-15, 9), (crest-8, 24)),
        bezier((crest-8, 24), (crest-4.5, 31.5), (crest-2.5, crown), (crest, crown)),
        bezier((crest, crown), (crest+2.4, crown), (crest+2.5, 32), (crest+3.0, 26)),
        bezier((crest+3.0, 26), (crest+3.6, 18.8), (crest+8, shelf), (crest+18, shelf)),
        cq.Edge.makeLine(p(crest+18, shelf), p(tip+2, shelf)),
    ]
    low = cq.Vector(0,0,-0.8)
    a, b = p(tip+2, 0)+low, p(foot, 0)+low
    edges.extend([cq.Edge.makeLine(p(tip+2, shelf), a),
                  cq.Edge.makeLine(a, b), cq.Edge.makeLine(b, p(foot,0))])
    return cq.Wire.assembleEdges(edges)


def build(side, output=OUT, shelf_adjust=None, section_shift=None):
    base = read(BASE/f'wing_{side}.step')
    intervals = [[START,-55,-80,-105,-130,-140,-150,FOLD_X],
                 [FOLD_X,(FOLD_X+RAMP_X)/2,RAMP_X],
                 [RAMP_X,-185,-200,-211,TAIL_X]]
    if section_shift is not None:
        # Sample the common-profile bend at close intervals to prevent loft overshoot.
        knots = [START,-55.,-80.,-105.,-125.,-140.,-155.,FOLD_X,RAMP_X,-185.,-202.,TAIL_X]
        intervals = [[a+(b-a)*j/5 for j in range(6)] for a,b in zip(knots,knots[1:])]
    sections = [cq.Solid.makeLoft([profile(side,x,shelf_adjust,section_shift) for x in xs]) for xs in intervals]
    raised = sections[0].fuse(*sections[1:]).intersect(wing_plan(side))
    result = base.fuse(raised).clean()
    assert result.isValid() and len(result.Solids()) == 1
    step = output/f'wing_{side}.step'
    cq.exporters.export(result, str(step))
    export = read(step)
    assert export.isValid() and len(export.Solids()) == 1
    export.exportStl(str(step.with_suffix('.stl')), tolerance=.025, angularTolerance=.06)
    print(side, export.BoundingBox().zmax, flush=True)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for side in SIGNS:
        build(side)
