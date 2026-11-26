#!/usr/bin/env python3
"""Conservatively bound deposited G-code curves with a line-width allowance."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import zipfile

TAU = 2 * math.pi
CARDINAL = ((0, 1, 0), (math.pi / 2, 0, 1), (math.pi, -1, 0), (math.pi * 1.5, 0, -1))
AXES = re.compile(r'([XYZEIJR])([-+]?(?:\d*\.)?\d+)')


def arc_bounds(ax, ay, bx, by, cx, cy, ccw):
    # Coordinates are printed to 0.001 mm. The programmed start/end radii can
    # therefore differ slightly. Enclose both radii at both angular endpoints.
    radius_a = math.hypot(ax - cx, ay - cy)
    radius_b = math.hypot(bx - cx, by - cy)
    if min(radius_a, radius_b) <= 0.0:
        raise ValueError("Arc radius is zero")
    a = math.atan2(ay - cy, ax - cx)
    b = math.atan2(by - cy, bx - cx)
    if ax == bx and ay == by:
        radius = max(radius_a, radius_b)
        return cx - radius, cy - radius, cx + radius, cy + radius
    direction = 1 if ccw else -1
    sweep = ((b - a) * direction) % TAU
    lo_x, lo_y, hi_x, hi_y = min(ax, bx), min(ay, by), max(ax, bx), max(ay, by)
    for angle, dx, dy in CARDINAL:
        if (angle - a) * direction % TAU <= sweep + 0.0000001:
            x = cx + dx * max(radius_a, radius_b)
            y = cy + dy * max(radius_a, radius_b)
            lo_x, lo_y, hi_x, hi_y = min(lo_x, x), min(lo_y, y), max(hi_x, x), max(hi_y, y)
    # Cover rounding discrepancies at endpoints and across the path.
    drift = abs(radius_b - radius_a)
    return lo_x - drift, lo_y - drift, hi_x + drift, hi_y + drift


def deposition(lines):
    x = y = z = e = 0.0
    relative_xyz, relative_e = False, True
    feature, started, width, layer_z = "Custom", False, None, None
    for lineno, line in enumerate(lines, 1):
        if line.startswith("; FEATURE:"):
            feature = line.partition(":")[2].strip()
        elif line.startswith("; LINE_WIDTH:"):
            width = float(line.partition(":")[2])
        elif line.startswith("; CHANGE_LAYER"):
            started = True
        elif line.startswith("; Z_HEIGHT:"):
            layer_z = float(line.partition(":")[2])
        elif line.startswith(("G", "M")):
            op, _, argsstr = line.partition(';')[0].strip().partition(' ')
            if op == "M82":
                relative_e = False
            elif op == "M83":
                relative_e = True
            elif op == "G90":
                relative_xyz = False
            elif op == "G91":
                relative_xyz = True
            elif op in ("G92", "G0", "G1", "G2", "G3"):
                args = {key: float(val) for key, val in AXES.findall(argsstr)}
                if op == "G92":
                    x, y, z, e = [args.get(key, val) for key, val in zip("XYZE", (x, y, z, e))]
                    continue
                ax, ay, az = x, y, z
                if "X" in args:
                    x = args["X"] + (x if relative_xyz else 0.0)
                if "Y" in args:
                    y = args["Y"] + (y if relative_xyz else 0.0)
                if "Z" in args:
                    z = args["Z"] + (z if relative_xyz else 0.0)
                if "E" not in args:
                    continue
                de = args["E"] if relative_e else args["E"] - e
                e += de
                if not started or feature == "Custom" or de <= 0 or (x == ax and y == ay and op in ("G0", "G1")):
                    continue
                if width is None or width <= 0.0 or layer_z is None:
                    raise ValueError(f"Missing valid width or layer metadata at line {lineno}")
                if "R" in args or (op in ("G2", "G3") and not any(a in args for a in "IJ")):
                    raise ValueError(f"Unsupported movement format at line {lineno}")
                arc = ((ax + args.get("I", 0.0), ay + args.get("J", 0.0), op == "G3") if op in ("G2", "G3") else None)
                yield lineno, feature, width, layer_z, (ax, ay, az), (x, y, z), arc


def check_gcode(lines):
    total = [math.inf, math.inf, -math.inf, -math.inf]
    first = total.copy()
    first_support = total.copy()
    zmin = zmax = None
    clear = math.inf
    violations = []
    count = Counter()
    min_first = math.inf
    n_arcs = 0
    clearance_at_extrema = {}
    for ln, feature, width, z_layer, (ax, ay, az), (x, y, z), arc in deposition(lines):
        if arc:
            lo_x, lo_y, hi_x, hi_y = arc_bounds(ax, ay, x, y, *arc)
            n_arcs += 1
        else:
            lo_x, lo_y, hi_x, hi_y = min(ax, x), min(ay, y), max(ax, x), max(ay, y)
        rad = width * 0.5 + 0.003
        bx = [lo_x - rad, lo_y - rad, hi_x + rad, hi_y + rad]
        for i, (start, value) in enumerate(zip(total, bx)):
            test = min if i <= 1 else max
            if test(start, value) != start:
                total[i] = value
                clearance_at_extrema[str(i)] = [ln, feature, z_layer]
        if z_layer < 0.201:
            first = [min(first[0], bx[0]), min(first[1], bx[1]), max(first[2], bx[2]), max(first[3], bx[3])]
            if feature == "Support":
                first_support = [min(first_support[0], bx[0]), min(first_support[1], bx[1]), max(first_support[2], bx[2]), max(first_support[3], bx[3])]
        zlo, zhi = min(az, z), max(az, z)
        zmin = zlo if zmin is None else min(zmin, zlo)
        zmax = zhi if zmax is None else max(zmax, zhi)
        count[feature] += 1
        # Distance between the artifact-conservative arc/line bounding box and
        # the printer's actual exclusion rectangle [0,18]×[0,28].
        dist = math.hypot(max(0.0, bx[0] - 18.0, -bx[2]), max(0.0, bx[1] - 28.0, -bx[3]))
        clear = min(clear, dist)
        if z_layer < 0.201:
            min_first = min(min_first, dist)
        if min(bx[0], bx[1], 256 - bx[2], 256 - bx[3], zlo, 250 - zhi) < 0 or dist == 0:
            violations.append({"line": ln, "feature": feature, "bbox": bx, "programmed_zz_mm": [zlo, zhi], "layer_mm": z_layer})
    return {
        "method": "G0 through G3 deposited model/support/brim trajectories, not printer start/end routines. Exact angular extrema of each G2/G3 arc plus start/end radius mismatch; conservative deposited envelope adds line width / 2 and 0.003 mm rounding allowance. Per-command bounding-box separation from exclusion rectangle.",
        "bed_print_volume_mm": [256, 256, 250],
        "excluded_xy_rectangle_mm": [0, 0, 18, 28],
        "total_extrusion_xy_bounds_mm": total,
        "first_layer_extrusion_xy_bounds_mm": first,
        "first_layer_support_xy_bounds_mm": first_support,
        "total_extrusion_z_bounds_mm": [zmin, zmax],
        "minimum_bed_edge_clearance_mm": min(total[0], total[1], 256 - total[2], 256 - total[3]),
        "minimum_exclusion_zone_clearance_lower_bound_mm": clear,
        "first_layer_exclusion_zone_clearance_lower_bound_mm": min_first,
        "deposition_commands_by_feature": dict(count),
        "arc_count": n_arcs,
        "violation_count": len(violations),
        "first_violations": violations[:20],
        "xy_bounds_extremal_commands": clearance_at_extrema,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("project", type=Path)
    ns = p.parse_args()
    with zipfile.ZipFile(ns.project) as z:
        out = {}
        for i in (1, 2):
            with z.open(f"Metadata/plate_{i}.gcode") as fp:
                out[i] = check_gcode(line.decode() for line in fp)
    print(json.dumps(out, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
