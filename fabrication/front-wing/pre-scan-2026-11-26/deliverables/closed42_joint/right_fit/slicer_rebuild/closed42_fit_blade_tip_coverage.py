#!/usr/bin/env python3
"""Probe support XY directly beneath the earliest printed free-edge paths."""
import json, math, zipfile, sys
from closed42_fit_gcode_qa import deposition


def pts(a,b,arc):
    ax,ay = a[:2]; bx,by = b[:2]
    if not arc:
        n = max(1,math.ceil(math.hypot(bx-ax,by-ay)/.035))
        return [(ax+(bx-ax)*j/n,ay+(by-ay)*j/n) for j in range(n+1)]
    cx,cy,ccw=arc
    a=math.atan2(ay-cy,ax-cx); b=math.atan2(by-cy,bx-cx)
    r=math.hypot(ax-cx,ay-cy)
    delta=(((b-a)%(2*math.pi)) if ccw else -((a-b)%(2*math.pi))) if (ax,ay)!=(bx,by) else (2*math.pi if ccw else -2*math.pi)
    n=max(1,math.ceil(abs(r*delta)/.035))
    return [(cx+r*math.cos(a+delta*j/n),cy+r*math.sin(a+delta*j/n)) for j in range(n)]+[(bx,by)]

p=json.load(open(sys.argv[2]))[0]
xc,yc,zc,rad=p
center=(xc+128,yc+128)
model=[]; layers = {}
with zipfile.ZipFile(sys.argv[1]) as z:
    with z.open('Metadata/plate_2.gcode') as fp:
        for ln, typ, width, layer_z, a,b,arc in deposition(line.decode() for line in fp):
            if 12.5 < layer_z < 14.2 and typ.startswith('Support'):
                points=[(xy, width*.5, ln) for xy in pts(a,b,arc) if math.dist(xy,center)<rad+3]
                if points: layers.setdefault(layer_z, []).extend(points)
            if abs(layer_z-14.2)<1e-6 and typ=='Overhang wall':
                points=[(xy, width*.5, ln) for xy in pts(a,b,arc) if math.dist(xy,center)<rad]
                model.extend(points)
def stats(z,support):
    raw=[(min(math.dist(m,s)-sr-mr for s,sr,_ in support),ln) for m,mr,ln in model]
    return {'method':'Sample actual XY deposition centerlines at ≤0.035 mm intervals and subtract both extrusion radii. Compare the first free-edge overhang wall with supporting toolpaths from below, including the nominal 0.28 mm air gap after accounting for model layer thickness. Positive sample edge-to-edge gap means no overlapping extrusion footprint for that point. Compare sample neighborhoods, not entire upper blade or physical output.', 'first_cad_edge_point_print_local_mm':p[:3], 'sampling_radius_mm':rad,'first_tip_model_z_mm':14.2,'support_z_mm':z,'support_source_commands':len({ln for _,_,ln in support}),'overhang_source_commands':len({ln for _,_,ln in model}),'sample_count':len(raw),'samples_with_xy_footprint_overlap':sum(g<=0 for g,_ in raw),'min_signed_xy_separation_mm':min(g for g,_ in raw),'max_signed_xy_separation_mm':max(g for g,_ in raw),'model_command_signed_separation_range_mm':{ln:[min(g for g,l in raw if l==ln),max(g for g,l in raw if l==ln)] for ln in sorted({l for _,l in raw})}}
print(json.dumps({str(z):stats(z,s) for z,s in layers.items()}, indent=2))
