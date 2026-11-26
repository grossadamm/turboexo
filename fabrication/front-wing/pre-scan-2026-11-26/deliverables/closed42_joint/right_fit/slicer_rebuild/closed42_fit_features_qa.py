#!/usr/bin/env python3
"""Compare support deposition with CAD-derived ROIs for this car-right fit."""
import argparse
import json
import math
from pathlib import Path
import re
import zipfile
from closed42_fit_gcode_qa import arc_bounds, deposition


def boxes_overlap(a, b):
    return a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]


def bounds(a, b, arc, width, c=(0, 0), u=(1, 0), v=(0, 1)):
    def local(p):
        dx, dy = p[0] - c[0], p[1] - c[1]
        return dx*u[0]+dy*u[1], dx*v[0]+dy*v[1]
    ax, ay = local(a)
    bx, by = local(b)
    if arc:
        cx, cy = local(arc)
        ccw = arc[2] if u[0]*v[1]-u[1]*v[0] > 0 else not arc[2]
        lo_x, lo_y, hi_x, hi_y = arc_bounds(ax, ay, bx, by, cx, cy, ccw)
    else:
        lo_x, lo_y, hi_x, hi_y = min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)
    d = width * 0.5 + 0.003
    return [lo_x-d, lo_y-d, hi_x+d, hi_y+d]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('project', type=Path)
    p.add_argument('cad_feature_probe', type=Path)
    p.add_argument('--blade-probe', type=Path)
    p.add_argument('--plates', nargs='+', type=int, choices=(1, 2), default=(1, 2))
    args = p.parse_args()
    lines = args.cad_feature_probe.read_text().splitlines()
    xyz = re.compile(r'\[(-?\d+(?:\.\d+)?), (-?\d+(?:\.\d+)?), (-?\d+(?:\.\d+)?)\]')
    features = {}
    for ln in lines:
        a, b = [tuple(map(float, v)) for v in xyz.findall(ln)]
        if ln.startswith('gap'):
            features.setdefault('gaps', []).append((a, b))
        else:
            features.setdefault('bores' if 'bore' in ln else 'sockets', []).append((ln.split()[0], (a, b)))
    blade_pts = json.loads(args.blade_probe.read_text()) if args.blade_probe else []
    out = {'bores': {}, 'sockets': {}, 'runner_gap_samples': [], 'blade': []}
    with zipfile.ZipFile(args.project) as z:
        for i in args.plates:
            center = (128, 132.4) if i == 1 else (128, 128)
            def xy(q):
                return (q[0] + center[0], q[1] + center[1])
            feat = []
            if i == 1:
                for name, (a,b) in features['bores']:
                    hit = out['bores'][name] = {'probe_xyz_bed_local_mm': [a,b], 'support_count': 0, 'first_hits': []}
                    # Cover entire slanted bore on XY, and include 0.28 mm Z slack.
                    ax, ay = xy(a)
                    bx, by = xy(b)
                    feat.append((hit, min(a[2],b[2])-.28, max(a[2],b[2])+.28, 'circle', ((ax+bx)/2,(ay+by)/2), 3.4+math.hypot(ax-bx,ay-by)/2))
            else:
                u = (0.8290375726, 0.5591929035)
                v = (0.5591929035,-0.8290375726)
                for name, (a,b) in features['sockets']:
                    hit = out['sockets'][name] = {'probe_xyz_bed_local_mm': [a,b], 'support_count': 0, 'first_hits': []}
                    feat.append((hit, a[2]-.28,b[2]+.28, 'rect', xy(a), (u, v, (-8.2,-3.2,8.2,3.2))))
                for a,b in features['gaps']:
                    ax, ay = xy(a)
                    bx, by = xy(b)
                    dist = math.hypot(bx-ax,by-ay)
                    u = ((bx-ax)/dist, (by-ay)/dist)
                    v = (-u[1],u[0])
                    hit = {'probe_xyz_bed_local_mm': [a,b], 'gap_width_mm': dist, 'support_count': 0, 'first_hits': []}
                    out['runner_gap_samples'].append(hit)
                    feat.append((hit, a[2]-.28, a[2]+.28, 'rect', xy(a),(u, v, (0.7,-0.2,dist-.7,.2))))
                for j, (lx, ly, lz, tol) in enumerate(blade_pts):
                    hit = {'probe_xyz_bed_local_mm': [lx,ly,lz], 'radius_mm': tol, 'nearby_model_layers': {}, 'nearby_support_layers': {}}
                    out['blade'].append(hit)
                    feat.append((hit, max(0,lz-0.7), lz+1.1, 'blade', xy((lx,ly)), tol))
            with z.open(f'Metadata/plate_{i}.gcode') as fp:
                for ln, typ, width, layer_z, a,b,arc in deposition(line.decode() for line in fp):
                    is_support = typ.startswith('Support')
                    for hit,z0,z1,test,c,params in feat:
                        if (not is_support and test != 'blade') or not z0 <= layer_z <= z1:
                            continue
                        if test == 'rect':
                            u,v,r = params
                            bb = bounds(a,b,arc,width,c,u,v)
                            if not boxes_overlap(bb,r):
                                continue
                        else:
                            bb = bounds(a,b,arc,width,c)
                            ds = math.hypot(max(0,bb[0],-bb[2]),max(0,bb[1],-bb[3]))
                            if ds > params:
                                continue
                        if test == 'blade':
                            key = 'nearby_support_layers' if is_support else 'nearby_model_layers'
                            d = hit[key].setdefault(layer_z,{})
                            if typ != "Brim":
                                d[typ] = d.get(typ,0)+1
                        else:
                            hit['support_count'] += 1
                            if len(hit['first_hits']) < 8:
                                hit['first_hits'].append({'gcode_line':ln,'feature':typ,'layer_z_mm':layer_z,'support_bounds_in_probe_xy_mm':bb})
    out['method'] = 'CAD-derived axial/section probes tested against conservative projected extrusion-command bounds and matching Z layers. Bore cylinders and socket rectangular envelopes conservatively enlarged at Z ends by 0.28 mm. Runner-gap section probes trim 0.7 mm at each CAD surface and use 0.2 mm orthogonal tolerance and 0.28 mm in Z. This section sampling is not a global boundary check.'
    print(json.dumps(out,indent=2))


if __name__ == '__main__':
    main()
