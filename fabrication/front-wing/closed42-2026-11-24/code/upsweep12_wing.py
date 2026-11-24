"""Roll the last 80 mm of the outboard shelf to a 12 degree exit."""
from math import radians, tan
from swept_ramp_wing import D, SIGNS, RUN, START, TAIL_X, TIP_RISE, build, top_z

OUT = D/'upsweep12_wing'
LENGTH = 80.0
JOIN = TAIL_X + LENGTH
EXIT_SLOPE = tan(radians(12))


def old_shelf(x):
    t = (START-x)/RUN
    return top_z(x)-.08+(TIP_RISE+.08)*t*t*(3-2*t)


def adjustment(x):
    if x >= JOIN:
        return 0.
    t0 = (START-JOIN)/RUN
    join_slope = (TIP_RISE+.08)*6*t0*(1-t0)/RUN
    t = (JOIN-x)/LENGTH
    # Integral of a slope easing from the old tangent to the specified exit.
    target = old_shelf(JOIN) + LENGTH*(join_slope*t +
             (EXIT_SLOPE-join_slope)*(t*t - t**3/3))
    return target-old_shelf(x)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    for side in SIGNS:
        build(side, OUT, adjustment)
