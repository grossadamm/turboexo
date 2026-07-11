#!/usr/bin/env python3
"""
Generate boost-extended VE / AFR / spark tables for the TurboExo Speeduino tune.

Usage:
    python3 generate_boost_tables.py [source.msq] [output.msq]

Reads the source tune (default: CurrentTune.msq — TunerStudio's LIVE working
tune, which it overwrites on every save), re-interpolates the sub-100 kPa
region onto the 16-point load axis below, computes the boost rows from first
principles, and writes ONE output:

    CurrentTune_BOOST_DRAFT_BARO.msq    (multiplyMAP=Baro, true-VE table)

Then run patch_commissioning_settings.py on that output to produce
TurboExo_FirstStart.msq — ALWAYS re-run the patch script after this one so the
commissioning/safety settings carry forward.

Intended workflow: after the NA region is road-tuned on the wideband,
CurrentTune.msq holds the tuned tune — re-run this script (no argument) to
regenerate the boost rows from real numbers, then re-run the patch script.

The script is axis-agnostic: it reads whatever load axes the source has and
only requires that interpolation at 100 kPa is meaningful (a tuned region
reaching 100 kPa). It is also multiplyMAP-mode-aware:
  - source multiplyMAP=Off  -> VE cells are PW-percent; converted to true VE
  - source multiplyMAP=Baro -> VE cells are already true VE; used as-is
so it can be re-run on its own (patched) output without double-converting.

Math basis (verified against Speeduino docs):
  PW = (MAP/Baro) * (VE/100) * reqFuel + deadtime          [multiplyMAP=Baro]
  incorporateAFR=No, so the AFR table does NOT affect open-loop fuel —
  boost richening must live in the VE numbers:
      VE_boost(rpm) = VE_100kPa_true(rpm) * (AFR_anchor(rpm) / AFR_target)
  where AFR_anchor(rpm) is the source AFR table's own 100 kPa target for that
  rpm column (what the tuned VE row is calibrated to deliver).

NOTE: afrTable and lambdaTable are dual views of the SAME firmware bytes
(mainController.ini: afrTable offset = lastOffset of lambdaTable). Both are
rewritten together here; shipping them inconsistent makes the burned values
depend on TunerStudio's load order.
"""
import re
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else \
    "/Users/adamgross/TunerStudioProjects/TurboExo/CurrentTune.msq"
DST = sys.argv[2] if len(sys.argv) > 2 else \
    "/Users/adamgross/TunerStudioProjects/TurboExo/CurrentTune_BOOST_DRAFT_BARO.msq"

# ---- new unified 16-point load axis (kPa) -------------------------------------
# bins 1-7 preserve idle/cruise resolution, 8-11 respaced toward WOT, 12-16 boost.
# bottom bin 20 kPa: in Baro mode VE=VE_old*(100/MAP) and 16 kPa overflowed the
# 255 cap (->lean on overrun). 86 (not 85): MAP bins store in 2 kPa steps, so
# TunerStudio quantizes 85->86 on save — 86 keeps re-runs round-trip stable.
NEW_LOAD = [20, 26, 30, 36, 40, 46, 50, 60, 70, 86, 100, 120, 140, 160, 180, 200]

# ---- boost-region targets -----------------------------------------------------
# AFR target per boost bin (pump 91, richen as boost climbs for knock/thermal margin)
AFR_BOOST = {120: 12.5, 140: 12.0, 160: 11.8, 180: 11.6, 200: 11.5}
SPARK_PULL_PER_KPA = 0.15  # deg removed per kPa above 100 (pump 91, conservative)
SPARK_FLOOR = 8.0          # never command less than this
VE_CAP = 255               # Speeduino VE cell hard limit

# ---- first-start / knock-blind shaping (2026-06-12 adversarial review) ---------
# KNOCK_BLIND: knock sensor is raw/unconditioned -> knock_mode Off. Until a
# conditioner is fitted, pull extra spark from every boost row on top of the
# per-kPa slope (140 kPa: ~22->18, 160: ~19->16). Set False once knock works.
KNOCK_BLIND = True
KNOCK_BLIND_EXTRA_PULL = 3.5   # deg, boost rows only
# FIRST_START_SHAPING: the unproven NA estimate has a lean trough in the 700 rpm
# column (VE 59-74 at 60-100 kPa, in the first-catch / stall-recovery path) and
# a destabilizing idle spark slope (advance falls as rpm sags below 1000). These
# FLOORS lift only the lean/low cells; richer source values pass through, and the
# 500 rpm rich catch cells are deliberately untouched. The 100 kPa floor also
# anchors the boost rows of that column. Set False when regenerating from a
# road-tuned NA tune (the wideband will have fixed the trough properly).
FIRST_START_SHAPING = True
VE_FLOOR_700RPM = {60: 95, 70: 90, 86: 85, 100: 80}   # load kPa -> min true VE
IDLE_SPARK_FLOOR = 16.0        # deg at the 500 rpm column, 30-46 kPa rows

# -------------------------------------------------------------------------------
def read(path):
    with open(path) as f:
        return f.read()

def grab(msq, name):
    """Return (full_match, opening_tag, inner_text, closing_tag) for a <constant>."""
    m = re.search(r'(<constant[^>]*\bname="%s"[^>]*>)(.*?)(</constant>)' % re.escape(name),
                  msq, re.DOTALL)
    if not m:
        raise KeyError(name)
    return m.group(0), m.group(1), m.group(2), m.group(3)

def nums(inner):
    return [float(x) for x in inner.split()]

def grid(vals, rows, cols):
    return [vals[r*cols:(r+1)*cols] for r in range(rows)]

def interp(xs, ys, x):
    """Linear interpolation, clamped at the ends. xs ascending."""
    if x <= xs[0]:
        return ys[0]
    if x >= xs[-1]:
        return ys[-1]
    for i in range(len(xs) - 1):
        if xs[i] <= x <= xs[i + 1]:
            t = (x - xs[i]) / (xs[i + 1] - xs[i])
            return ys[i] + t * (ys[i + 1] - ys[i])
    return ys[-1]

def col(g, c):
    return [row[c] for row in g]

# -------------------------------------------------------------------------------
msq = read(SRC)

# --- source mode and fuel ------------------------------------------------------
_, _, mode_inner, _ = grab(msq, "multiplyMAP")
SRC_MODE = mode_inner.strip().strip('"')
if SRC_MODE not in ("Off", "Baro"):
    raise SystemExit("Unsupported source multiplyMAP mode: %r" % SRC_MODE)

_, _, stoich_inner, _ = grab(msq, "stoich")
STOICH = float(stoich_inner)

# --- pull the three tables, their load axes, and verify dimensions -------------
_, _, ve_inner, _   = grab(msq, "veTable")
_, _, fl_inner, _   = grab(msq, "fuelLoadBins")
_, _, afr_inner, _  = grab(msq, "afrTable")
_, _, al_inner, _   = grab(msq, "loadBinsAFR")
_, _, adv_inner, _  = grab(msq, "advTable1")
_, _, ml_inner, _   = grab(msq, "mapBins1")

ve   = grid(nums(ve_inner), 16, 16)   # rows = load (asc), cols = rpm (asc)
afr  = grid(nums(afr_inner), 16, 16)
adv  = grid(nums(adv_inner), 16, 16)
fuel_load = nums(fl_inner)            # 16
afr_load  = nums(al_inner)            # 16
spark_load = nums(ml_inner)           # 16

assert len(fuel_load) == 16 and len(afr_load) == 16 and len(spark_load) == 16

NCOLS = 16

_, _, rpm_inner, _ = grab(msq, "rpmBins")
rpm = nums(rpm_inner)
COL_500 = next((c for c in range(NCOLS) if rpm[c] < 600), None)
COL_700 = next((c for c in range(NCOLS) if 600 <= rpm[c] < 800), None)

def ve_true_at(c, load):
    """True VE (Baro-mode semantics) for rpm column c at a given load, from source.
    Applies the first-start lean-trough floor to the 700 rpm column (idempotent:
    floors are max(), so re-running on shaped output changes nothing)."""
    v = interp(fuel_load, col(ve, c), float(load))
    if SRC_MODE == "Off":
        # Off-mode cells are PW-percent (no MAP multiply): VE_true = VE_old * (100/MAP)
        v = v * (100.0 / load)
    if FIRST_START_SHAPING and c == COL_700 and load in VE_FLOOR_700RPM:
        v = max(v, VE_FLOOR_700RPM[load])
    return v

def afr_anchor(c):
    """Source AFR-table target at 100 kPa for rpm column c (what VE_100 delivers)."""
    return interp(afr_load, col(afr, c), 100.0)

# --- build the three new 16x16 grids on NEW_LOAD --------------------------------
new_ve, new_afr, new_spark = [], [], []
for load in NEW_LOAD:
    ve_row, afr_row, spk_row = [], [], []
    for c in range(NCOLS):
        if load <= 100:
            ve_row.append(min(round(ve_true_at(c, load)), VE_CAP))
            afr_row.append(round(interp(afr_load, col(afr, c), float(load)), 1))
            spk = interp(spark_load, col(adv, c), float(load))
            if FIRST_START_SHAPING and c == COL_500 and 30 <= load <= 46:
                spk = max(spk, IDLE_SPARK_FLOOR)
            spk_row.append(round(spk))
        else:
            ve100 = ve_true_at(c, 100)
            ve_row.append(min(round(ve100 * (afr_anchor(c) / AFR_BOOST[load])), VE_CAP))
            afr_row.append(AFR_BOOST[load])
            spk100 = interp(spark_load, col(adv, c), 100.0)
            pull = SPARK_PULL_PER_KPA * (load - 100)
            if KNOCK_BLIND:
                pull += KNOCK_BLIND_EXTRA_PULL
            spk_row.append(round(max(spk100 - pull, SPARK_FLOOR)))
    new_ve.append(ve_row)
    new_afr.append(afr_row)
    new_spark.append(spk_row)

# lambdaTable mirrors afrTable byte-for-byte in firmware: lambda = AFR / stoich
new_lambda = [[round(v / STOICH, 7) for v in row] for row in new_afr]

# --- emit replacement inner-text in the msq's whitespace style -----------------
def fmt_grid(g, fmt="%.1f"):
    lines = ["\n"]
    for row in g:
        lines.append("         " + " ".join(fmt % v for v in row) + " \n")
    lines.append("      ")
    return "".join(lines)

def fmt_lambda_grid(g):
    lines = ["\n"]
    for row in g:
        lines.append("         " + " ".join(str(v) for v in row) + " \n")
    lines.append("      ")
    return "".join(lines)

def fmt_axis(vals):
    lines = ["\n"]
    for v in vals:
        lines.append("         %.1f \n" % v)
    lines.append("      ")
    return "".join(lines)

def replace_block(msqt, name, new_inner):
    full, open_tag, _old_inner, close_tag = grab(msqt, name)
    return msqt.replace(full, open_tag + new_inner + close_tag, 1)

def set_scalar(msqt, name, value):
    full, open_tag, _inner, close_tag = grab(msqt, name)
    return msqt.replace(full, open_tag + ("%.1f" % value) + close_tag, 1)

# ---- SAFETY PATCHES ------------------------------------------------------------
# Confirmed gaps (adversarially verified against speeduino.ini help text):
#   - knock ignored above 100 kPa / 1000 rpm, total retard capped at 1deg
#   - iatRetRates all zero -> no IAT-based timing retard
# IAT timing retard: conservative, no pull until intake is hot, then ~1deg/10F.
IAT_RET_BINS  = [110, 130, 150, 170, 190, 210]   # deg F
IAT_RET_RATES = [0,   2,   4,   6,   8,   10]     # deg timing removed
# Knock coverage: extend window over the whole boost/rev range so the system CAN
# protect in boost once a conditioner is fitted (knock_mode itself is set by the
# patch script). maxRetard kept modest to limit false-positive damage.
KNOCK_MAXMAP = 250.0   # was 100
KNOCK_MAXRPM = 7000.0  # was 1000
KNOCK_MAXRET = 4.0     # was 1

out = msq
out = replace_block(out, "veTable",      fmt_grid(new_ve))
out = replace_block(out, "afrTable",     fmt_grid(new_afr))
out = replace_block(out, "lambdaTable",  fmt_lambda_grid(new_lambda))
out = replace_block(out, "advTable1",    fmt_grid(new_spark))
out = replace_block(out, "fuelLoadBins", fmt_axis(NEW_LOAD))
out = replace_block(out, "loadBinsAFR",  fmt_axis(NEW_LOAD))
out = replace_block(out, "mapBins1",     fmt_axis(NEW_LOAD))
out = replace_block(out, "multiplyMAP",  '"Baro"')
out = replace_block(out, "iatRetBins",   fmt_axis(IAT_RET_BINS))
out = replace_block(out, "iatRetRates",  fmt_axis(IAT_RET_RATES))
out = set_scalar(out, "knock_maxMAP",    KNOCK_MAXMAP)
out = set_scalar(out, "knock_maxRPM",    KNOCK_MAXRPM)
out = set_scalar(out, "knock_maxRetard", KNOCK_MAXRET)

with open(DST, "w") as f:
    f.write(out)

# --- verification dump ----------------------------------------------------------
def show(title, g):
    print("\n=== %s ===" % title)
    print("kPa\\rpm " + " ".join("%5d" % int(r) for r in rpm))
    for load, row in zip(NEW_LOAD, g):
        mark = "  <-- BOOST" if load > 100 else ""
        print("%6d  " % load + " ".join("%5.1f" % v for v in row) + mark)

print("Source: %s  (multiplyMAP=%s, stoich=%.1f)" % (SRC, SRC_MODE, STOICH))
print("NEW LOAD AXIS (kPa):", NEW_LOAD)
show("VE table (true VE, multiplyMAP=Baro)", new_ve)
show("AFR target", new_afr)
show("Spark advance", new_spark)

# fuel-preservation check: PW multiplier must match the source at sub-100 loads.
#   new (Baro):   PW ~ (load/100) * VE_true_new/100
#   source Off:   PW ~ VE_old/100        source Baro: PW ~ (load/100)*VE_src/100
print("\n--- fuel-preservation spot-checks vs source (PW multiplier) ---")
worst = 0.0
shaped = []
for load in [l for l in NEW_LOAD if l <= 100]:
    r = NEW_LOAD.index(load)
    for c in range(NCOLS):
        pw_new = (load / 100.0) * new_ve[r][c] / 100.0
        v_src = interp(fuel_load, col(ve, c), float(load))
        pw_src = (v_src / 100.0) if SRC_MODE == "Off" else (load / 100.0) * v_src / 100.0
        if FIRST_START_SHAPING and c == COL_700 and load in VE_FLOOR_700RPM:
            if pw_src > 0 and pw_new > pw_src * 1.005:
                shaped.append("%d kPa: VE floor lifted fuel +%.0f%%"
                              % (load, (pw_new / pw_src - 1) * 100))
            continue  # deliberate enrichment, not a preservation error
        if pw_src > 0:
            worst = max(worst, abs(pw_new - pw_src) / pw_src * 100)
print("  worst-case fuel delta across all sub-100 cells: %.2f%% (rounding only)" % worst)
for s in shaped:
    print("  first-start shaping, 700 rpm col @ %s (intentional)" % s)
if worst > 2.0:
    raise SystemExit("FUEL PRESERVATION CHECK FAILED (>2%% delta) — do not use output")

print("\nWrote: %s" % DST)
print("Now run patch_commissioning_settings.py to produce TurboExo_FirstStart.msq.")
print("%s was NOT modified." % SRC)
