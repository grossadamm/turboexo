#!/usr/bin/env python3
"""Analyze a TunerStudio/Speeduino datalog CSV for the TurboExo project.

Convert first:  npx mlg-converter --format=csv DataLogs/<file>.mlg
Then:           python scripts/analyze_log.py DataLogs/<file>.csv [more.csv ...]

Baked-in gotcha: logged AFR is NOT trustworthy mixture data on short catches. The
Spartan wideband is in warmup and Speeduino echoes live O2 into AFR Target, so AFR
mirrors AFR Target (fixed cal voltages ~13.1-13.2). This script reports that echo
fraction so you don't tune fuel from it. Judge fueling by effective fuel
(PW - injOpen) and by reading the plugs, not by logged AFR.
"""
import csv
import sys
import statistics as stats

INJ_OPEN_MS = 0.9        # injOpen (injector dead time) in CurrentTune.msq
FIRING_RPM = 400         # RPM above which the engine is "firing"
FLOOD_CLEAR_TPS = 90     # TPS >= this => flood-clear (fuel cut); excluded from fuel stats
RAN_BATT_V = 13.0        # battery >= this while firing => alternator charging => truly ran

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
    """Effective fuel per squirt = PW - dead time (approx real fuel delivered)."""
    pw = rec.get("pw")
    return None if pw is None else max(pw - INJ_OPEN_MS, 0.0)


def analyze(path):
    data, idx = load(path)
    name = path.split("/")[-1]
    if not data:
        print(f"\n=== {name}: no data rows / unrecognized format ===")
        return
    missing = [k for k in ("rpm", "map", "pw", "batt_v") if k not in idx]
    if missing:
        print(f"\n=== {name}: WARNING missing expected columns {missing} ===")

    dur = (data[-1]["time"] - data[0]["time"]) if idx.get("time") is not None else float("nan")
    firing = [r for r in data if (r.get("rpm") or 0) > FIRING_RPM]
    closed = [r for r in firing if (r.get("tps") or 0) < 5]
    cracked = [r for r in firing if 8 <= (r.get("tps") or 0) < FLOOD_CLEAR_TPS]

    batt_all = [r["batt_v"] for r in data if r.get("batt_v") is not None]
    batt_fire = [r["batt_v"] for r in firing if r.get("batt_v") is not None]
    ran = bool(batt_fire and max(batt_fire) >= RAN_BATT_V)

    print(f"\n=== {name}  rows={len(data)}  dur={dur:.1f}s ===")
    print(f"  Battery V: {_fmt(_stat(batt_all))}"
          + (f"  | firing max {max(batt_fire):.1f}" if batt_fire else ""))
    print(f"  TRULY RAN (batt>={RAN_BATT_V:.0f}V while firing = alternator charging): "
          f"{'YES' if ran else 'no'}")
    if idx.get("sync") is not None:
        s = f"  Sync status max={max((r.get('sync') or 0) for r in data):.0f}"
        if idx.get("sync_loss") is not None:
            s += f"  SyncLoss max={max((r.get('sync_loss') or 0) for r in data):.0f}"
        print(s)

    print(f"  Firing rows (RPM>{FIRING_RPM}): {len(firing)}")
    if firing:
        print(f"    RPM      {_fmt(_stat([r['rpm'] for r in firing]))}")
        print(f"    MAP      {_fmt(_stat([r['map'] for r in firing]), ' kPa')}")
        print(f"    eff.fuel {_fmt(_stat([_eff(r) for r in firing]), ' ms')}  (PW-{INJ_OPEN_MS})")
        if idx.get("gammae") is not None:
            print(f"    Gammae   {_fmt(_stat([r['gammae'] for r in firing]), '%')}")
        if idx.get("afr") is not None and idx.get("afr_target") is not None:
            pairs = [(r["afr"], r["afr_target"]) for r in firing
                     if r.get("afr") is not None and r.get("afr_target") is not None]
            if pairs:
                echo = sum(1 for a, t in pairs if abs(a - t) < 0.05)
                print(f"    AFR      {_fmt(_stat([a for a, _ in pairs]))}  "
                      f"[echo: AFR==Target in {echo}/{len(pairs)} = {100*echo/len(pairs):.0f}% "
                      f"-> NOT mixture]")

    if closed:
        print(f"  Closed throttle (TPS<5): {len(closed)} | "
              f"MAP {_fmt(_stat([r['map'] for r in closed]), ' kPa')} | "
              f"eff.fuel {_fmt(_stat([_eff(r) for r in closed]), ' ms')}")
    if cracked:
        print(f"  Cracked throttle (8<=TPS<{FLOOD_CLEAR_TPS}): {len(cracked)} | "
              f"MAP {_fmt(_stat([r['map'] for r in cracked]), ' kPa')} | "
              f"eff.fuel {_fmt(_stat([_eff(r) for r in cracked]), ' ms')}")


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
