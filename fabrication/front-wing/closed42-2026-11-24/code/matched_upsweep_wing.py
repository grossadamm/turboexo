"""Carry the outboard channel crest, shelf and bottom on one side-profile datum."""
from pathlib import Path
from tempfile import TemporaryDirectory
import cadquery as cq
from swept_ramp_wing import D, SIGNS, TAIL_X, WHEEL_Y, TIP_RISE, build, wing_plan, read
from upsweep36_wing import adjustment, shelf, old_shelf, JOIN
from skin_first_wing import wing_exterior
from twin_spar_wing import side_box

OUT = D/'matched_upsweep_wing'
CROWN_ABOVE_SHELF = 16.
EDGE_DEPTH = 10.


def smooth(t):
    u = max(0.,min(1.,t))
    return u*u*(3.-2.*u)


def shift(x,y,crest,width,rise,blend):
    if x >= JOIN or rise == 0:
        return 0.
    weight = smooth((y-crest+width)/width)
    # Transition the old crown/shelf separation to the constant section.
    blend_in = smooth((JOIN-x)/35.)
    crown_change = (CROWN_ABOVE_SHELF-25.*blend)*blend_in
    if y >= crest:
        fraction = max(0.,(rise-TIP_RISE-.08)/25.)
    else:
        fraction = rise/40.08
    return adjustment(x)*weight + fraction*crown_change


def bottom_section(side,x):
    tip = abs(WHEEL_Y[side])
    skin = shelf(x) if x < JOIN else old_shelf(x)
    start = smooth((-65.-x)/65.)
    height = 115. + start*(skin-EDGE_DEPTH-115.)
    # Keep clearance below the straight aft socket. Behind it, widen the
    # turned-under return across the rear outer panel.
    aft = smooth((-179.-x)/30.)
    inner = -20.5-44*aft
    knee = -15.-25*aft
    def at(y,z):
        return cq.Vector(x,SIGNS[side]*(tip+y),z)
    a,b,c = at(inner,115.), at(knee,height), at(3,height)
    lo,li = at(3,50.), at(inner,50.)
    return cq.Wire.assembleEdges([
        cq.Edge.makeBezier([a,at(inner+(knee-inner)*.37,115.),at(knee-(knee-inner)*.37,height),b]),
        cq.Edge.makeLine(b,c),cq.Edge.makeLine(c,lo),cq.Edge.makeLine(lo,li),cq.Edge.makeLine(li,a)])


def make(side,tmp):
    build(side,tmp,section_shift=shift)
    part = read(tmp/f'wing_{side}.step')
    tip = abs(WHEEL_Y[side])
    backing = wing_exterior(side,wing_plan(side)).intersect(
        side_box(side,TAIL_X-1,-179.8,tip-68,tip+2,80,180))
    # Separate smooth lofts at the ends of each blending interval.
    sections = [[-65,-80,-95,-105,-116,-124,-130],[-130,-140,-150,-160,-170,-178,-179],
                [-179,-183,-188,-194,-200,-206,-209],[-209,-213,-217,-220,-220.2]]
    cuts = [cq.Solid.makeLoft([bottom_section(side,x) for x in group]) for group in sections]
    result = part.fuse(backing).cut(*cuts).clean()
    assert result.isValid() and len(result.Solids()) == 1
    step = OUT/f'wing_{side}.step'
    cq.exporters.export(result,str(step))
    checked=read(step)
    assert checked.isValid() and len(checked.Solids()) == 1
    checked.exportStl(str(step.with_suffix('.stl')),tolerance=.025,angularTolerance=.07)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    with TemporaryDirectory() as stage:
        for side in SIGNS:
            make(side,Path(stage))
