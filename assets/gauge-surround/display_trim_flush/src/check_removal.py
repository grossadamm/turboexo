"""Bound continuous base clearance on the released fascia's removal path."""
import json
import math

import cadquery as cq
import numpy as np
from OCP.BRepExtrema import BRepExtrema_DistShapeShape

import build_trim as m
from validate_trim import PIVOT_Y, TRIM_PATH


def main():
    base = m.to_local(cq.importers.importStep(str(m.OUT/"surround.step")).val())
    released = m.to_local(cq.importers.importStep(str(m.OUT/"display_trim.step")).val())
    box = released.BoundingBox()
    radius = math.hypot(max(abs(box.ymin-PIVOT_Y),abs(box.ymax-PIVOT_Y)),
                        max(abs(box.zmin),abs(box.zmax)))
    distance = BRepExtrema_DistShapeShape()
    distance.LoadS2(base.wrapped)
    distance.SetMultiThread(True)

    def base_clearance(part):
        distance.LoadS1(part.wrapped)
        assert distance.Perform() and distance.IsDone()
        return distance.Value()

    target = .12
    samples = []
    cells = []
    for start,end in zip(TRIM_PATH,TRIM_PATH[1:]):
        start,end = np.asarray(start),np.asarray(end)
        change = end-start
        # A point at distance r from the pivot moves by at most r*dtheta.
        # Set-to-set clearance changes by no more than the maximum point motion.
        speed = float(np.linalg.norm(change[1:])) + radius*abs(math.radians(change[0]))
        pending = [(0.,1.)]
        while pending:
            lo,hi = pending.pop()
            t = (lo+hi)/2
            angle,x,y,z = start+t*change
            pose = [angle,x,y,z]
            moved = released.rotate((0,PIVOT_Y,0),(1,PIVOT_Y,0),angle).translate((x,y,z))
            clearance = base_clearance(moved)
            assert clearance > target and hi-lo > 1e-5, (pose,clearance)
            lower = clearance - speed*(hi-lo)/2
            samples.append((clearance,pose))
            if lower >= target:
                cells.append(lower)
            else:
                pending.extend(((lo,t),(t,hi)))
    minimum,pose = min(samples)
    result = dict(continuous_base_clearance_lower_bound_mm=min(cells),
                  distance_samples=len(samples), certified_subintervals=len(cells),
                  minimum_sampled_base_clearance_mm=minimum, minimum_sampled_pose=pose)
    (m.OUT/"continuous_removal_check.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__ == "__main__":
    main()
