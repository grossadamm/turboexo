"""Matched 3D blade-on 16° vs 30° postprocessing, in solver coordinates.

Run after compare_flow.py has written the two 30° cases. No new flow solve is
performed. Uses existing matched axes and interpolates the saved cell-center
velocity vectors, not the staggered x-face velocities in compare_flow.py.
Missing any corner of an interpolation stencil returns NaN, so no borrowing
from obstacles or from unmatched portions of a comparison patch.
"""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
from scipy.interpolate import RegularGridInterpolator

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1] / "cfd_corner_study"
sys.path.insert(0, str(BASE))
from geometry import _ray_hits, mesh_triangles

GRIDS = ("1.5", "1")
ANGLES = (16, 30)
CASES = [(h, a) for h in GRIDS for a in ANGLES]
SLOT = 205.0
STATIONS = [30, 100, 145, 185, 200, 205, 215, 225, 228, 260, 320, 395]
WINDOWS = {
    "legacy_slot_not_geometry_matched": (205, 550, 568, 187.5, 194.5),
    "exit_patch": (228, 547, 576, 197, 220),
    "approach_broad": (395, 550, 635, 175, 265),
    "approach_wing_lane": (395, 550, 585, 175, 215),
    "approach_upper_wing_lane": (395, 550, 585, 215, 265),
    "approach_outer_lane": (395, 585, 635, 175, 215),
    "approach_upper_outer_lane": (395, 585, 635, 215, 265),
}


def read_stl(path):
    dt = np.dtype([("normal", "<f4", 3), ("points", "<f4", (3, 3)), ("tag", "<u2")])
    with path.open("rb") as f:
        f.seek(80)
        n = int.from_bytes(f.read(4), "little")
        cells = np.fromfile(f, count=n, dtype=dt)
        if len(cells) != n or f.read(1):
            raise ValueError(f"Expected a binary STL at {path}")
    return cells["points"] * [-1.0, -1.0, 1.0]


def compared_meshes(args):
    settings = [json.loads((HERE / f"{h}_1_30.json").read_text()) for h in GRIDS]
    if settings[0]["stl_inputs"] != settings[1]["stl_inputs"]:
        raise ValueError("30° cases did not use identical geometry")
    cache_hash = sha256((BASE / "geometry_meshes.npz").read_bytes()).hexdigest()
    if any(d["geometry_cache_sha256"] != cache_hash for d in settings):
        raise ValueError("Shared geometry cache differs from the one used for the flow solves")
    swept = []
    for p, k in [(args.control, "wing_control"), (args.blade, "upper_blade")]:
        spec = settings[0]["stl_inputs"][k]
        path = Path(p).resolve() if p else HERE / spec["file"]
        if sha256(path.read_bytes()).hexdigest() != spec["sha256"]:
            raise ValueError(f"{path} differs from the geometry used for the flow solves")
        swept.append(read_stl(path))
    return {16: (mesh_triangles("wing_control"), mesh_triangles("upper_blade")),
            30: tuple(swept)}, settings[0]["stl_inputs"]


def profiles(meshes, x, y):
    """CAD projected upper floor and lower roof at a fixed rearward station."""
    ans = []
    for i, tri in enumerate(meshes):
        ids, d = _ray_hits(tri, np.array([x+0.000137]), y-0.000293)
        n, start, count = np.unique(ids, return_index=True, return_counts=True)
        out = np.full(len(y), np.nan)
        out[n] = d[start+(count-1 if i == 0 else 0)]
        ans.append(out)
    return ans


def stats(v, area):
    if not len(v) or np.sum(area) <= 0:
        return None
    u = v[:, 0]
    w = area*np.maximum(0, u)
    total = w.sum()
    if total <= 0:
        return None
    mean = np.average(v, axis=0, weights=w)
    return dict(area_mm2=float(area.sum()), forward_flux_mm2_U=float(total),
                mean_velocity_U=mean.tolist(), up_deg=float(angles(mean)[0]),
                out_deg=float(angles(mean)[1]))


def angles(v):
    return np.stack((np.degrees(np.arctan2(v[..., 2], v[..., 0])),
                     np.degrees(np.arctan2(v[..., 1], v[..., 0]))), axis=-1)


def pointwise_angle_delta(new, reference):
    return (angles(new)-angles(reference)+180.) % 360.-180.


def velocities(f, x, yz):
    return f(np.column_stack((np.full(len(yz), x), yz)))


def finite(v):
    return np.isfinite(v).all(axis=-1)


def window(x, ylo, yhi, zlo, zhi, sampling=0.25):
    edges = [np.linspace(lo, hi, int(np.ceil((hi-lo)/sampling))+1)
             for lo, hi in [(ylo, yhi), (zlo, zhi)]]
    a, b = [(e[1:]+e[:-1])/2 for e in edges]
    yz = np.column_stack([p.ravel() for p in np.meshgrid(a, b, indexing="ij")])
    return yz, np.prod([np.diff(e)[0] for e in edges]), (len(a), len(b))


def deltas(b, a):
    if not a or not b:
        return None
    return {k: float(b[k]-a[k]) for k in ["up_deg", "out_deg", "forward_flux_mm2_U"]}


def build_windows(mesh):
    y = np.arange(515., 590.001, 0.05)
    raw = {a: profiles(mesh[a], SLOT, y) for a in ANGLES}
    span = {a: y[np.isfinite(raw[a][1])][[0, -1]] for a in ANGLES}
    # Roots differ, so the fixed patch must be inside both CAD slot spans.
    # Also keep 3 mm away from each lateral edge and 3 mm above/below the
    # floor/roof across the whole rectangle. Prefer the historical slot y-window.
    ylo = np.ceil(2*max(550, *[p[0]+3 for p in span.values()]))/2
    yhi = np.floor(2*min(568, *[p[1]-3 for p in span.values()]))/2
    k = (y >= ylo-0.025) & (y <= yhi+0.025)
    if yhi <= ylo or not np.all([finite(np.stack((lo[k], hi[k]), axis=-1)).all()
                               for lo, hi in raw.values()]):
        raise ValueError("No valid common lateral span")
    zlo = np.ceil(2*(max(p[0][k].max() for p in raw.values())+3))/2
    zhi = np.floor(2*(min(p[1][k].min() for p in raw.values())-3))/2
    if zhi <= zlo:
        raise ValueError("No valid common vertical span")
    common = (SLOT, ylo, yhi, zlo, zhi)
    return span, common


def compare_relative(fields, mesh, span):
    report = {}
    # Same x, same fraction of each roof's CAD span, and the same central
    # fraction of its own floor-to-roof height at each sampled y.
    for name, (ell, urr) in {"slot_relative": (0.50, 0.75),
                            "slot_relative_inner": (0.43, 0.58),
                            "slot_relative_outer": (0.67, 0.82)}.items():
        probes = {}
        for a in ANGLES:
            ya, yb = span[a][0]+np.ptp(span[a])*np.array([ell, urr])
            n, m = 48, 24
            y = ya+(yb-ya)*(np.arange(n)+0.5)/n
            lo, hi = profiles(mesh[a], SLOT, y)
            dz = hi-lo
            if not np.isfinite(dz).all() or np.min(dz) <= 0:
                raise ValueError(f"Invalid CAD slot clearance in {name} at {a}°")
            z = lo[:, None]+dz[:, None]*(0.35+0.3*(np.arange(m)+0.5)/m)
            yz = np.column_stack((np.repeat(y, m), z.ravel()))
            darea = np.repeat((yb-ya)/n*dz*0.3/m, m)
            probes[a] = (yz, darea, dict(y_mm=[float(ya), float(yb)],
                                        floor_mm=[float(lo.min()), float(lo.max())],
                                        roof_mm=[float(hi.min()), float(hi.max())],
                                        clearance_mm=[float(dz.min()), float(dz.max())],
                                        sampled_z_mm=[float(z.min()), float(z.max())]))
        samples = {(h, a): velocities(f, SLOT, probes[a][0]) for (h, a), f in fields.items()}
        matched = np.logical_and.reduce([finite(v) for v in samples.values()])
        if name == "slot_relative" and not matched.all():
            raise ValueError("Primary slot-relative patch intersects an invalid interpolation stencil")
        bygrid = {}
        for h in GRIDS:
            both = {a: stats(samples[h, a][matched], probes[a][1][matched]) for a in ANGLES}
            bygrid[h] = {**both, "delta_30_minus_16": deltas(both[30], both[16])}
        report[name] = dict(station_mm=SLOT, lateral_fraction=[ell, urr],
                            floor_to_roof_fraction=[0.35, 0.65],
                            support_fraction=float(matched.mean()),
                            CAD_geometry={a: probes[a][2] for a in ANGLES}, bygrid=bygrid)
    return report


def compare_fixed(fields, win, strict=False):
    x, *bounds = win
    yz, area, shape = window(x, *bounds)
    v = {k: velocities(f, x, yz) for k, f in fields.items()}
    valid = np.logical_and.reduce([finite(p) for p in v.values()])
    if strict and not valid.all():
        raise ValueError(f"Probe at {win} intersects a non-fluid interpolation stencil")
    d = {}
    diffs = {}
    for h in GRIDS:
        both = {a: stats(v[h, a][valid], np.full(valid.sum(), area)) for a in ANGLES}
        vec = v[h, 30][valid]-v[h, 16][valid]
        diffs[h] = pointwise_angle_delta(v[h, 30][valid], v[h, 16][valid])
        d[h] = {**both, "delta_30_minus_16": deltas(both[30], both[16]),
                "pointwise_absolute_delta_p50_p95_max_deg_up_out":
                    np.quantile(np.abs(diffs[h]), [0.50, 0.95, 1.0], axis=0).tolist() if valid.any() else None,
                "pointwise_rms_delta_vector_speed_U":
                    float(np.sqrt(np.mean(np.sum(vec**2, axis=-1)))) if valid.any() else None,
                "pointwise_rms_delta_component_speed_uvw_U":
                    np.sqrt(np.mean(vec**2, axis=0)).tolist() if valid.any() else None}
    if valid.sum() > 3:
        agreement = np.mean(np.sign(diffs["1"]) == np.sign(diffs["1.5"]), axis=0).tolist()
        error = np.sqrt(np.mean((diffs["1"]-diffs["1.5"])**2, axis=0)).tolist()
    else:
        agreement = error = None
    return dict(station_ylo_yhi_zlo_zhi_mm=list(win), common_fluid_area_mm2=float(valid.sum()*area),
                mean_support_fraction=float(valid.mean()), bygrid=d,
                cross_grid_pointwise_delta_sign_agreement_fraction_up_out=agreement,
                cross_grid_pointwise_delta_rms_difference_deg_up_out=error)


def trace(f, x0, x1, seeds, step):
    yz = seeds.copy()
    x_axis = np.linspace(x0, x1, int(np.ceil(abs(x1-x0)/step))+1)
    path = [yz.copy()]

    def deriv(x, yz):
        v = velocities(f, x, yz)
        return np.divide(v[:, 1:], v[:, :1], out=np.full_like(yz, np.nan), where=v[:, :1] > 0.12)

    for x, xx in zip(x_axis[:-1], x_axis[1:]):
        dx = xx-x
        k = deriv(x, yz)
        l = deriv(x+dx/2, yz+dx*k/2)
        m = deriv(x+dx/2, yz+dx*l/2)
        n = deriv(xx, yz+dx*m)
        yz = yz+dx/6*(k+2*l+2*m+n)
        path.append(yz.copy())
    return x_axis, np.array(path)


def paired_traces(fields, mesh, x0, seeds, sector, step=0.5, only_through_slot=False):
    runs = {k: trace(f, x0, 395., seeds, step) for k, f in fields.items()}
    x = runs["1", 16][0]
    j = int(np.argmin(abs(x-SLOT)))
    slot = dict()
    survived = {k: finite(p[-1]) for k, (_, p) in runs.items()}
    for k, (_, p) in runs.items():
        # Sample the actual slot floor and roof for this geometry. Exclude
        # splinter rays near the exact root/tip and require 1 mm CAD clearance.
        ya = np.arange(510., 590.05, 0.1)
        lo, hi = profiles(mesh[k[1]], SLOT, ya)
        y, z = p[j].T
        lower, upper = np.interp(y, ya, lo), np.interp(y, ya, hi)
        slot[k] = (z > lower+1) & (z < upper-1)
    crossed_all = np.logical_and.reduce(list(slot.values()))
    matched = np.logical_and.reduce(list(survived.values()))
    if only_through_slot:
        matched &= crossed_all
    d = {"start_station_mm": x0, "streamwise_step_mm": step,
         "physical_seed_window_mm": sector, "seed_count": len(seeds),
         "slot_crossing_counts_by_case": {f"{h}_{a}": int(v.sum()) for (h, a), v in slot.items()},
         "tire_station_survivor_counts_by_case": {f"{h}_{a}": int(v.sum()) for (h, a), v in survived.items()},
         "crossed_own_CAD_slot_in_all_four": int(crossed_all.sum()),
         "matched_survivors": int(matched.sum()), "only_through_slot_cohort": only_through_slot,
         "bygrid": {}}
    c = {}
    for h in GRIDS:
        d["bygrid"][h] = selected = {}
        for s in [s for s in STATIONS if s >= x0]:
            i = np.argmin(abs(x-s))
            if not matched.any():
                continue
            y16 = runs[h, 16][1][i, matched]
            y30 = runs[h, 30][1][i, matched]
            delta = y30-y16
            selected[s] = dict(mean_yz_16_mm=y16.mean(0).tolist(),
                               mean_yz_30_mm=y30.mean(0).tolist(),
                               delta_yz_mm=delta.mean(0).tolist(),
                               delta_yz_mm_p10_p50_p90=np.quantile(delta, [0.1, 0.5, 0.9], axis=0).tolist())
        if matched.any():
            c[h] = {a: runs[h, a][1][:, matched].mean(1) for a in ANGLES}
            for a in ANGLES:
                y_end, z_end = runs[h, a][1][-1, matched].T
                selected[395][f"{a}_endpoint_coverage"] = {
                    "y_min_max_mm": [float(y_end.min()), float(y_end.max())],
                    "z_min_max_mm": [float(z_end.min()), float(z_end.max())],
                    "count_outboard_of_tire_inboard_datum_y585p1": int(np.sum(y_end >= 585.1)),
                    "count_inside_broad_approach_probe": int(np.sum(
                        (y_end >= 550) & (y_end <= 635) & (z_end >= 175) & (z_end <= 265))),
                }
    return d, (x, c), (matched, {k: p[-1] for k, (_, p) in runs.items()})


def load_fields():
    fields, axes, hashes = {}, {}, {}
    for h, a in CASES:
        p = BASE / f"{h}_1_on.npz" if a == 16 else HERE / f"{h}_1_30.npz"
        digest = sha256(p.read_bytes()).hexdigest()
        if a == 16:
            rerun = HERE / f"{h}_1_16.npz"
            if rerun.exists() and sha256(rerun.read_bytes()).hexdigest() != digest:
                raise ValueError(f"Current reference solve {rerun} differs from original {p}")
        hashes[f"{h}_{a}"] = digest
        with np.load(p) as q:
            xyz = tuple(q[k] for k in ("s", "y", "z"))
            xyz_base = axes.setdefault(h, xyz)
            if any(not np.array_equal(v, b) for v, b in zip(xyz, xyz_base)):
                raise ValueError(f"Grids did not match for {p}")
            v = np.stack([q[k] for k in ("u", "v", "w")], axis=-1)
            if not np.array_equal(finite(v), np.isfinite(v[..., 0])):
                raise ValueError(f"Nonfinite velocities inconsistent for {p}")
        fields[h, a] = RegularGridInterpolator(xyz, v, bounds_error=False,
                                               fill_value=np.nan)
    return fields, hashes


def plot_maps(fields):
    panels = [WINDOWS["exit_patch"], WINDOWS["approach_broad"]]
    fig, axes = plt.subplots(2, 2, figsize=(9, 6.8), constrained_layout=True)
    for r, win in enumerate(panels):
        x, ya, yb, za, zb = win
        yz, _, shape = window(*win, sampling=0.5)
        v = {k: velocities(f, x, yz) for k, f in fields.items()}
        valid = np.logical_and.reduce([finite(p) for p in v.values()])
        changes = pointwise_angle_delta(v["1", 30], v["1", 16])
        changes[~valid] = np.nan
        for j, name in enumerate(("up", "outboard")):
            a = axes[r, j]
            data = changes[:, j].reshape(shape).T
            lim = max(np.nanmax(abs(data)), 0.001)
            im = a.imshow(np.ma.masked_invalid(data), origin="lower", extent=(ya, yb, za, zb),
                          cmap="RdBu_r", norm=TwoSlopeNorm(0, -lim, lim), aspect="equal")
            a.set_title(f"x = {x} mm · Δ {name}")
            a.set_xlabel("Outboard y (mm)")
            a.set_ylabel("Height z (mm)")
            if r == 1:
                a.axvline(585, c="k", ls=":", lw=0.8, alpha=.7)
                a.axhline(215, c="k", ls=":", lw=0.8, alpha=.7)
            fig.colorbar(im, ax=a, shrink=.90, label="30° minus 16° (deg)")
    fig.suptitle("Right-front model · local direction change on the 1 mm grid\n"
                 "Exit and wheel approach use different color scales")
    fig.savefig(HERE / "sweep_direction_differences.png", dpi=190)
    plt.close(fig)


def plot_traces(groupings):
    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, constrained_layout=True)
    styles = {"slot-fed upstream cohort": "-", "matched in-slot starts": "--"}
    colors = {"1": "#087f8c", "1.5": "#ad4428"}
    for name, (x, centers) in groupings.items():
        for h, models in centers.items():
            delta = models[30]-models[16]
            for j, ax in enumerate(axes):
                ax.plot(x, delta[:, j], color=colors[h], ls=styles[name],
                        label=f"{h} mm · {name}")
    for ax, label in zip(axes, ("outboard", "upward")):
        for s, msg in [(205, "slot"), (228, "behind lip"), (395, "tire approach")]:
            ax.axvline(s, color=".65", lw=.85, zorder=0)
            if ax is axes[0]:
                ax.annotate(msg, (s, 1.005), textcoords="offset points", xytext=(0, 0),
                            xycoords=("data", "axes fraction"), ha="center", fontsize=8)
        ax.axhline(0, color=".75", lw=.85, zorder=0)
        ax.set_ylabel(f"Δ {label} position (mm)")
        ax.grid(axis="y", alpha=.16)
    axes[0].legend(fontsize=8, loc="best")
    axes[1].set_xlabel("Rearward x (mm)")
    fig.suptitle("Matched model streamlines · 30° minus 16° mean displacement\n"
                 "Every traced endpoint remains inboard of the tire-approach patch")
    fig.savefig(HERE / "sweep_matched_streamlines.png", dpi=190)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--control", type=Path, help="Override the original 30° floor/control STL location")
    parser.add_argument("--blade", type=Path, help="Override the original 30° upper blade STL location")
    args = parser.parse_args()
    fields, hashes = load_fields()
    mesh, geometry_inputs = compared_meshes(args)
    span, common = build_windows(mesh)
    report = dict(
        coordinate_system="x rearward, y car-right outboard, z up; mm",
        sources={f"{h}_{a}": f"{'../../cfd_corner_study/' if a == 16 else ''}{h}_1_{'on' if a == 16 else a}.npz"
                 for h, a in CASES},
        source_field_sha256=hashes,
        source_30_geometry=geometry_inputs,
        probe_notes="Saved cell-center vectors interpolated linearly and averaged with positive rearward flux weighting. "
                    "Angle is calculated from a weighted mean vector, not from individually averaged angles. "
                    "Each physical comparison uses one shared fluid support across both geometries and both grids. "
                    "At corresponding slot-relative samples, support is shared in normalized coordinates and integrated "
                    "with each actual geometry's area element, not projected back to a fixed physical rectangle. "
                    "Local percentiles of absolute pointwise angle changes and RMS velocity changes are unweighted by mass flux.",
        CAD_roof_projected_span_y_at_x205_mm={k: v.tolist() for k, v in span.items()},
    )
    report["fixed_probes"] = {name: compare_fixed(fields, win) for name, win in WINDOWS.items()}
    report["fixed_probes"]["slot_common"] = compare_fixed(fields, common, strict=True)
    report["relative_probes"] = compare_relative(fields, mesh, span)
    for name, d in {**report["fixed_probes"], **report["relative_probes"]}.items():
        print(name, d.get("mean_support_fraction", d.get("support_fraction")), {
            h: {**v["delta_30_minus_16"], "rms_delta_U": v.get("pointwise_rms_delta_vector_speed_U")}
            for h, v in d["bygrid"].items() if v["delta_30_minus_16"] is not None}, flush=True)

    initial_sector = (515., 550., 138., 172.)
    initial, _, _ = window(30., *initial_sector, sampling=0.75)
    # Same physical starts before the crest diverges. Representatives must
    # cross their own CAD slot and reach x=395 at both grids in both variants.
    upstream, up_plot, up_ends = paired_traces(fields, mesh, 30., initial, initial_sector,
                                      only_through_slot=True)
    slot_initial, _, _ = window(*common, sampling=0.75)
    slot, slot_plot, slot_ends = paired_traces(fields, mesh, SLOT, slot_initial, common[1:])
    # Half-step RK4 sensitivity using identical seeds and all-four selection.
    for data, x0, seeds, bounds, filt, (original_ok, original_xyz) in [
        (upstream, 30., initial, initial_sector, True, up_ends),
        (slot, SLOT, slot_initial, common[1:], False, slot_ends)
    ]:
        half, _, (short_ok, short_xyz) = paired_traces(
            fields, mesh, x0, seeds, bounds, step=0.25, only_through_slot=filt)
        ok = original_ok & short_ok
        max_diff = {f"{h}_{a}": float(np.max(np.linalg.norm(
            original_xyz[h, a][ok]-short_xyz[h, a][ok], axis=-1)))
            for h, a in CASES} if ok.any() else None
        data["half_step_rk4_check"] = dict(
            matched_survivors=half["matched_survivors"],
            same_survivor_at_both_steps_count=int(ok.sum()),
            max_endpoint_step_sensitivity_mm=max_diff,
            tire_station_delta_yz_mm={h: half["bygrid"][h].get(395, {}).get("delta_yz_mm")
                                      for h in GRIDS})
    report["streamlines"] = dict(upstream_slot_fed=upstream, matched_in_slot=slot)
    (HERE / "sweep_matched_metrics.json").write_text(json.dumps(report, indent=2)+"\n")
    for name, d in report["streamlines"].items():
        print(name, d["matched_survivors"], "/", d["seed_count"],
              {h: d["bygrid"][h].get(395, {}) for h in GRIDS}, flush=True)
    plot_maps(fields)
    plot_traces({"slot-fed upstream cohort": up_plot, "matched in-slot starts": slot_plot})


if __name__ == "__main__":
    main()
