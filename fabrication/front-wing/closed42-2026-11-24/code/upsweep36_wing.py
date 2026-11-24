"""Rolled wheel-side lip with clearance for the existing straight spar sockets."""
from math import radians, tan
from tempfile import TemporaryDirectory
from pathlib import Path
import cadquery as cq
from swept_ramp_wing import D, SIGNS, RUN, START, TAIL_X, TIP_RISE, WHEEL_Y, build, wing_plan, read
from skin_first_wing import wing_exterior
from twin_spar_wing import side_box
from upsweep12_wing import old_shelf

OUT = D/'upsweep36_wing'
JOIN = -105.
RUN_UP = JOIN-TAIL_X
EXIT = tan(radians(36))


def shelf(x):
    t = (JOIN-x)/RUN_UP
    join_t = (START-JOIN)/RUN
    initial = (TIP_RISE+.08)*6*join_t*(1-join_t)/RUN
    return old_shelf(JOIN) + RUN_UP*(initial*t + (EXIT-initial)*(.7*t*t - .4*t**3/3))


def adjustment(x):
    return shelf(x)-old_shelf(x) if x < JOIN else 0.


def relief_section(side, x):
    # Hermite underside starts below the blade behind the aft spar and meets
    # the level of the raised lip with a 10 mm vertical edge and matching tangent.
    t = (-178-x)/42
    start = 119.
    z = start + (shelf(TAIL_X)-10-start)*(3*t*t-2*t**3) + 42*EXIT*(t**3-t*t)
    tip = abs(WHEEL_Y[side])
    def at(offset,height):
        return cq.Vector(x,SIGNS[side]*(tip+offset),height)
    a,b,c,d = at(-60,115),at(-37,z),at(3,z),at(3,40)
    e = at(-60,40)
    return cq.Wire.assembleEdges([
        cq.Edge.makeBezier([a,at(-52,115),at(-45,z),b]),
        cq.Edge.makeLine(b,c),cq.Edge.makeLine(c,d),cq.Edge.makeLine(d,e),cq.Edge.makeLine(e,a)])


def make(side, tmp):
    build(side, tmp, adjustment)
    part = read(tmp/f'wing_{side}.step')
    tip = abs(WHEEL_Y[side])
    backing = wing_exterior(side,wing_plan(side)).intersect(
        side_box(side,TAIL_X-1,-179.8,tip-63,tip+2,80,180))
    tool = cq.Solid.makeLoft([relief_section(side,x) for x in (-178,-185,-194,-203,-212,-220,-220.1)])
    result = part.fuse(backing).cut(tool).clean()
    assert result.isValid() and len(result.Solids()) == 1
    target = OUT/f'wing_{side}.step'
    cq.exporters.export(result,str(target))
    check = read(target)
    assert check.isValid() and len(check.Solids()) == 1
    check.exportStl(str(target.with_suffix('.stl')),tolerance=.025,angularTolerance=.07)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    with TemporaryDirectory() as stage:
        for side in SIGNS:
            make(side,Path(stage))
