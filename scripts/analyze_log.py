#!/usr/bin/env python3
"""Analyze a TunerStudio/Speeduino datalog CSV for the TurboExo project.

Convert first:  npx mlg-converter --format=csv DataLogs/<file>.mlg
Then:           python scripts/analyze_log.py DataLogs/<file>.csv [more.csv ...]

Baked-in gotcha: logged AFR is NOT trustworthy mixture data on short catches. The
Spartan wideband is in warmup and Speeduino echoes live O2 into AFR Target, so AFR
mirrors AFR Target (fixed cal voltages ~13.1-13.3). This script reports that echo
fraction so you don't tune fuel from it. Judge fueling by effective fuel (PW minus a
voltage-corrected dead time) and by reading the plugs, not by logged AFR.
"""
import csv
import sys
import statistics as stats

INJ_OPEN_MS = 0.9        # injOpen (~12 V dead time) in CurrentTune.msq; fallback only
FIRING_RPM = 400         # above cranking, below a real idle => a "catch"/firing row
FLOOD_CLEAR_TPS = 90     # tpsflood: TPS >= this cuts PW *during cranking* (flood clear)
RAN_BATT_V = 13.0        # battery >= this while firing suggests the alternator is charging
RAN_MIN_ROWS = 3         # require this many such rows before calling it a sustained run

# Measured RX-8 yellow (Denso 195500-4450) injector dead time vs voltage (ms), from
# docs/REFERENCE.md. Dead time is strongly voltage-dependent, so a flat PW - injOpen
# overstates delivered fuel at cranking voltage; interpolate by the row's Battery V.
DEADTIME_V = [(6.5, 3.03), (7.75, 2.02), (9.0, 1.48), (10.25, 1.15),
              (11.5, 0.86), (12.75, 0.70), (14.0, 0.55)]

# canonical field -> accepted header spellings (matched after normalization)
FIELDS = {
    "time": ["Time"],
    "rpm": ["RPM"],
    "map": ["MAP"],
    "tps": ["TPS"],
    "afr": ["AFR"],
    "afr_target": ["AFR Target"],
    "ve": ["VE _Current", "VE Current"],
    "pw": ["PW"],
    "gammae": ["Gammae"],
    "gwarm": ["Gwarm"],
    "batt_v": ["Battery V"],
    "clt": ["CLT"],
    "sync": ["Sync status"],
    "sync_loss": ["Sync Loss #"],
}


def _norm(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _build_index(header):
    norm = {_norm(h): i for i, h in enumerate(header)}
    idx = {}
    for key, names in FIELDS.items():
        for n in names:
            j = norm.get(_norm(n))
            if j is not None:
                idx[key] = j
                break
    return idx


def deadtime_ms(volts):
    """Injector dead time (ms) interpolated from the measured curve by battery volts."""
    if volts is None:
        return INJ_OPEN_MS
    pts = DEADTIME_V
    if volts <= pts[0][0]:
        return pts[0][1]
    if volts >= pts[-1][0]:
        return pts[-1][1]
    for (v0, d0), (v1, d1) in zip(pts, pts[1:]):
        if v0 <= volts <= v1:
            return d0 + (d1 - d0) * (volts - v0) / (v1 - v0)
    return INJ_OPEN_MS


def load(path):
    with open(path, newline="") as f:
        rows = list(csv.reader(f, delimiter=";"))
    if len(rows) < 3:
        return [], {}
    idx = _build_index(rows[0])          # row0 = names, row1 = units, row2+ = data
    max_i = max(idx.values(), default=0)
    data = []
    for r in rows[2:]:
        if len(r) <= max_i:
            continue
        rec = {}
        for k, j in idx.items():
            try:
                rec[k] = float(r[j])
            except (ValueError, IndexError):
                rec[k] = None
        data.append(rec)
    return data, idx


def _stat(vals):
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return min(vals), max(vals), stats.mean(vals)


def _fmt(triple, unit=""):
    if triple is None:
        return "n/a"
    lo, hi, mean = triple
    return f"{lo:.1f}..{hi:.1f}{unit} (mean {mean:.1f})"


def _eff(rec):
    """Effective fuel per squirt = PW - voltage-corrected dead time (~delivered fuel)."""
    pw = rec.get("pw")
    if pw is None:
        return None
    return max(pw - deadtime_ms(rec.get("batt_v")), 0.0)


def analyze(path):
    data, idx = load(path)
    name = path.split("/")[-1]
    if not data:
        print(f"\n=== {name}: no data rows / unrecognized format ===")
        return
    missing = [k for k in ("rpm", "map", "pw", "batt_v") if k not in idx]
    if missing:
        print(f"\n=== {name}: WARNING missing expected columns {missing} ===")

    t0, t1 = data[0].get("time"), data[-1].get("time")
    dur = (t1 - t0) if (t0 is not None and t1 is not None) else float("nan")

    firing = [r for r in data if r.get("rpm") is not None and r["rpm"] > FIRING_RPM]
    closed = [r for r in firing if r.get("tps") is not None and r["tps"] < 5]
    cracked = [r for r in firing if r.get("tps") is not None and 5 <= r["tps"] < FLOOD_CLEAR_TPS]

    batt_all = [r["batt_v"] for r in data if r.get("batt_v") is not None]
    batt_fire = [r["batt_v"] for r in firing if r.get("batt_v") is not None]
    ran_rows = sum(1 for v in batt_fire if v >= RAN_BATT_V)
    ran = ran_rows >= RAN_MIN_ROWS

    print(f"\n=== {name}  rows={len(data)}  dur={dur:.1f}s ===")
    print(f"  Battery V: {_fmt(_stat(batt_all))}"
          + (f"  | firing max {max(batt_fire):.1f}" if batt_fire else ""))
    print(f"  Alternator likely charged? (heuristic: >={RAN_MIN_ROWS} firing rows "
          f">={RAN_BATT_V:.0f} V): {'likely' if ran else 'no'} ({ran_rows} rows)"
          f"  [a jump pack ~13 V can false-positive]")
    if idx.get("sync") is not None:
        syncs = [r["sync"] for r in data if r.get("sync") is not None]
        line = f"  Sync status max={max(syncs):.0f}" if syncs else "  Sync status: n/a"
        losses = [r["sync_loss"] for r in data if r.get("sync_loss") is not None]
        if losses:
            line += f"  SyncLoss max={max(losses):.0f}"
        print(line)

    print(f"  Firing rows (RPM>{FIRING_RPM}): {len(firing)}")
    if firing:
        print(f"    RPM      {_fmt(_stat([r['rpm'] for r in firing]))}")
        print(f"    MAP      {_fmt(_stat([r['map'] for r in firing]), ' kPa')}")
        print(f"    eff.fuel {_fmt(_stat([_eff(r) for r in firing]), ' ms')}  "
              f"(PW - V-corrected dead time)")
        if idx.get("gammae") is not None:
            print(f"    Gammae   {_fmt(_stat([r['gammae'] for r in firing]), '%')}")
        if idx.get("afr") is not None and idx.get("afr_target") is not None:
            pairs = [(r["afr"], r["afr_target"]) for r in firing
                     if r.get("afr") is not None and r.get("afr_target") is not None]
            if pairs:
                echo = sum(1 for a, t in pairs if abs(a - t) < 0.05)
                print(f"    AFR      {_fmt(_stat([a for a, _ in pairs]))}  "
                      f"[echo: AFR==Target {echo}/{len(pairs)} = {100*echo/len(pairs):.0f}% "
                      f"-> warmup echo, NOT mixture]")

    if closed:
        print(f"  Closed throttle (TPS<5): {len(closed)} | "
              f"MAP {_fmt(_stat([r['map'] for r in closed]), ' kPa')} | "
              f"eff.fuel {_fmt(_stat([_eff(r) for r in closed]), ' ms')}")
    if cracked:
        print(f"  Cracked throttle (5<=TPS<{FLOOD_CLEAR_TPS}): {len(cracked)} | "
              f"MAP {_fmt(_stat([r['map'] for r in cracked]), ' kPa')} | "
              f"eff.fuel {_fmt(_stat([_eff(r) for r in cracked]), ' ms')}")
    # TPS>=FLOOD_CLEAR_TPS firing rows are WOT enrichment / flood-clear: they appear in
    # the top-line firing eff.fuel but are excluded from the closed/cracked split above.


def main(argv):
    if not argv:
        print(__doc__)
        return 1
    for p in argv:
        try:
            analyze(p)
        except FileNotFoundError:
            print(f"\n=== {p}: file not found ===")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
