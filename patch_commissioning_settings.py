#!/usr/bin/env python3
"""
Apply commissioning-safety settings to the TurboExo boost draft tune.

Reads CurrentTune_BOOST_DRAFT_BARO.msq (read-only) and writes
TurboExo_FirstStart.msq with the changes below. Deterministic and
re-runnable; run it again after generate_boost_tables.py regenerates the draft
so these settings persist into future revisions.

Why each change (researched against speeduino wiki/forum + miataturbo.net,
verified against this project's mainController.ini — see BOOST_TUNE_NOTES.md):

  knock_mode -> Off            Raw piezo sensor is wired directly to the analog
                               input; Speeduino needs a conditioned 0-5V signal
                               (TPIC8101 module / Phormula KS-4). As-is it can
                               only produce noise-triggered retard and false
                               confidence. Re-enable Analog mode only after a
                               conditioner is installed and threshold calibrated.
  engineProtectType -> Both    Was "Spark Only": a spark-only protection cut on a
                               turbo keeps injecting fuel into a hot exhaust.
  afrProtect -> Fixed mode     Lean-spike backstop (wideband is wired to the ECU).
                               Window: >=124 kPa (was 180 — ABOVE the 160 boost
                               cut, i.e. could never trigger), >=2500 rpm,
                               >=50% TPS. Cut when AFR leaner than 13.0 for 1.0s.
                               124 kPa is unreachable NA, so no nuisance cuts
                               while NA tuning. (MAP stored in 2 kPa steps.)
  mapSample -> Cycle Average   ini help itself: "For more than 2 cylinders Cycle
                               Average is recommended". Instantaneous = spiky load.
  boostEnabled -> Off          Commissioning runs on wastegate spring only
                               (FIRST_START_CHECKLIST.md phases 5-6). Re-enable
                               for the boost ramp phase.
  engineProtectMaxRPM -> 1500  Was 7000 — ABOVE the 6800 hard rev limit. Per the
                               ini: "At this RPM and below, engine protections
                               will NOT be active", so the boost cut and AFR
                               lean-cut could NEVER fire. 1500 (not higher): the
                               firmware gates the BOOST cut behind this too, and
                               a lugging low-rpm WOT pull can overboost on the
                               small TD03L turbine; protection events also limp
                               the engine to this rpm. AFR protect keeps its own
                               2500 rpm floor, so no nuisance lean-cuts.
  perToothIgn -> Yes           'Use new ignition mode' — the Speeduino wiki page
                               for the Miata 99-05 decoder requires it; with only
                               4 crank teeth/rev, timing otherwise scatters
                               several degrees during cranking/transients.
  primingDelay -> 3 s          Was 0: the one-shot priming squirt fired into an
                               unpressurized dry rail at key-on, before fpPrime
                               built pressure — wasting the dry-port wetting fix.
  crankingEnrichTaper -> 1.5 s Was 0.1: fueling stepped down ~35% in 0.1 s at the
                               crank-to-run handoff, inviting a stall at catch.
  Accel enrichment block       aeTime/taeThresh/taeMinChange/aeTaperMin/aeTaperMax
                               were ALL ZEROS: aeTaperMax=0 fully tapers AE away
                               at all RPM (lean tip-in stumble), and
                               decelAmount=0 cuts ALL fuel momentarily on every
                               throttle close (ini: 100% = no reduction).
                               Starting values: 150 ms AE, trigger 50 %/s with
                               2% min TPS change, taper 1000->5000 rpm,
                               decelAmount 100%. (taeRates curve 43/49/74/113%
                               was already populated.)
  wueRates curve               Was ALL ZEROS — fatal: WUE is a fuel multiplier
                               (100% = no change) and clamps to the last value,
                               so total correction = 0 -> pulsewidth = 0 -> no
                               fuel at ANY coolant temp. Generic BP starting
                               curve, 160% at -40F tapering to 100% warm
                               (ECU_FIRST_START_AUDIT.md). Bins unchanged.
  fpPrime -> 3 s               Was 0: fuel pump never primed at key-on.
  primePulse curve             Was all zeros. Single priming squirt at powerup,
                               temp-scaled; helps first catch with 425cc injectors.
  ASE (afterstart enrichment)  Was all zeros: engine catches then stalls lean.
                               Standard starting values, taper over a few seconds.
  ADCFILTER_*                  Were all 0 (raw, noisy reads). Set to the values
                               recommended in mainController.ini help text
                               (BARO from firmware defaultValue; no help entry).

All curve/enrichment values are STARTING estimates to be tuned on the engine.
"""
import re
import xml.etree.ElementTree as ET

SRC = "/Users/adamgross/TunerStudioProjects/TurboExo/CurrentTune_BOOST_DRAFT_BARO.msq"
DST = "/Users/adamgross/TunerStudioProjects/TurboExo/TurboExo_FirstStart.msq"

# ---- scalar / string settings:  name -> (new value, kind) ---------------------
STRINGS = {
    "knock_mode":        "Off",
    "engineProtectType": "Both",
    "afrProtectEnabled": "Fixed mode",
    "mapSample":         "Cycle Average",
    "boostEnabled":      "Off",
    "perToothIgn":       "Yes",  # 'Use new ignition mode' — required by the
                                 # Miata 99-05 decoder wiki page; 4 teeth/rev
                                 # otherwise schedules spark off stale predictions
    "iacPWMrun":         "Yes",  # run the idle valve before RPM sync while
                                 # cranking — ini: "can help starting the engine
                                 # by letting more air in"
}
SCALARS = {
    "afrProtectMAP":             124.0,  # kPa (2 kPa storage steps; was 180)
    "afrProtectRPM":             2500.0,
    "afrProtectTPS":             50.0,   # % (was 80 — part-throttle boost uncovered)
    "afrProtectDeviation":       13.0,   # Fixed mode: absolute max AFR
    "afrProtectDeviationLambda": 0.884,  # same firmware byte, 13.0/14.7
    "afrProtectCutTime":         1.0,    # s
    "fpPrime":                   3.0,    # s pump prime at key-on
    "aseTaperTime":              2.0,    # s
    "engineProtectMaxRPM":       1500.0, # rpm floor for ALL protections (was 7000 — dead;
                                         # 1500 not 2500: firmware gates the BOOST cut here
                                         # too, and a lugging 2200-2500 rpm WOT pull can
                                         # overboost on the small TD03L turbine. Protection
                                         # events also limp to this rpm.)
    "primingDelay":              3.0,    # s — fire priming pulse AFTER fpPrime pressurizes
                                         # the rail (was 0 = squirt into 0-psi dry rail)
    "crankingEnrichTaper":       1.5,    # s — blend ~175-195% cranking fuel into ASE/run
                                         # over the catch flare (was 0.1 = abrupt 35% step)
    "idleTaperTime":             1.0,    # s — ease idle valve from crank duty (83%) to the
                                         # run table instead of snapping at catch (was 0)
    # --- 2026-06-12 coverage sweep (50-agent full-constant review) ---
    "tachoDuration":             2.0,    # ms — was 0 (below ini min 1): dead dash tach in
                                         # Fixed Duration mode; 2 = firmware default
    "boostSens":                 2000.0, # was 65535 (0xFFFF uninitialized, 13x ini max!) —
                                         # the LIVE closed-loop gain when Phase 7 enables
                                         # boost; 65535 would slam the MAC valve between
                                         # extremes. 2000 = firmware default.
    "boostIntv":                 30.0,   # ms — was 100; ini guidance: 50-100% of the valve
                                         # period. PID corrects every cycle instead of
                                         # every ~3.4 cycles on spool.
    "boostFreq":                 30.0,   # Hz — was 34: at/past the practical ceiling for
                                         # MAC 35A-type 3-port valves (response times eat
                                         # the duty window; community Miata builds run
                                         # 19.5-26 Hz; msextra reports control loss >33 Hz).
                                         # 2 Hz storage steps. REQUIRES ECU POWER-CYCLE.
    "dwellLim":                  8.0,    # ms — was 7.0 (exactly at the floor: wiki rule is
                                         # max dwell >= cranking dwell + 3 ms = 4+3 = 7).
                                         # 8.0 matches the official NB8B tune and gives
                                         # headroom for low-battery dwell correction.
    "aeColdPct":                 100.0,  # % — was 0 (AE x0 multiplier when cold). Inert
                                         # today only because the cold taper temps were
                                         # -40/-40; 100 = no adjustment (defuses the trap).
    "aeColdTaperMin":            32.0,   # F — firmware default cold-taper window
    "aeColdTaperMax":            140.0,  # F
    "aeTime":                    150.0,  # ms accel-enrichment duration (10 ms steps)
    "taeThresh":                 50.0,   # %/s TPS rate to trigger AE
    "taeMinChange":              2.0,    # % min TPS change for AE (0.5% steps)
    "aeTaperMin":                1000.0, # rpm: AE taper start
    "aeTaperMax":                5000.0, # rpm: AE fully tapered (was 0 = AE always zero)
    "decelAmount":               100.0,  # % fuel on decel; 100 = no cut (was 0 = full cut)
    "ADCFILTER_TPS":             50.0,
    "ADCFILTER_CLT":             180.0,
    "ADCFILTER_IAT":             180.0,
    "ADCFILTER_O2":              128.0,
    "ADCFILTER_BAT":             128.0,
    "ADCFILTER_MAP":             20.0,   # only used in Instantaneous mode; set anyway
    "ADCFILTER_BARO":            64.0,
}
# ---- 4-point curves (temp deg F ascending) ------------------------------------
CURVE_TEMP_BINS = [-40.0, 30.0, 100.0, 180.0]
CURVES = {
    "primeBins": CURVE_TEMP_BINS,
    "primePulse": [8.0, 6.0, 4.0, 2.0],   # ms, 0.5 ms storage steps
    "aseBins":   CURVE_TEMP_BINS,
    "asePct":    [35.0, 28.0, 18.0, 10.0],  # % added fuel after start
    "aseCount":  [10.0, 8.0, 5.0, 3.0],     # s duration
    # WUE: multiplier (100 = no change), existing 10 bins -40..171F kept as-is
    "wueRates":  [160.0, 154.0, 148.0, 142.0, 132.0, 122.0, 114.0, 108.0, 103.0, 100.0],
    # injector close-angle curve was all zeros (injection ended at TDC-firing instead
    # of just before the intake event) — restore firmware defaults
    "injAngRPM": [500.0, 2000.0, 4500.0, 6500.0],
    "injAng":    [355.0, 355.0, 355.0, 355.0],
    # boost target table TPS axis was stored DESCENDING (invalid bin order for the
    # firmware's table lookup; masked today only because all rows are identical)
    "tpsBinsBoost": [0.0, 20.0, 40.0, 60.0, 70.0, 80.0, 90.0, 100.0],
    # per-channel fuel trims: enable is No (and only live under Sequential layout),
    # but the stored payload was -128% = full lean cut on every channel if ever
    # enabled. Neutralize to 0% trim. Axes stay unset until trims are really used.
    "fuelTrim1Table": [0.0] * 36,
    "fuelTrim2Table": [0.0] * 36,
    "fuelTrim3Table": [0.0] * 36,
    "fuelTrim4Table": [0.0] * 36,
}

# ---- helpers (same pattern as generate_boost_tables.py) -----------------------
def grab(msq, name):
    m = re.search(r'(<constant[^>]*\bname="%s"[^>]*>)(.*?)(</constant>)' % re.escape(name),
                  msq, re.DOTALL)
    if not m:
        raise KeyError("constant not found in msq: %s" % name)
    return m.group(0), m.group(1), m.group(2), m.group(3)

def fmt_axis(vals):
    return "\n" + "".join("         %.1f \n" % v for v in vals) + "      "

def replace_inner(msq, name, new_inner):
    full, open_tag, _old, close_tag = grab(msq, name)
    return msq.replace(full, open_tag + new_inner + close_tag, 1)

def main():
    with open(SRC) as f:
        msq = f.read()

    changes = []  # (name, old, new)

    for name, val in STRINGS.items():
        _, _, old, _ = grab(msq, name)
        new = '"%s"' % val
        msq = replace_inner(msq, name, new)
        changes.append((name, old.strip(), new))

    for name, val in SCALARS.items():
        _, _, old, _ = grab(msq, name)
        digits = 3 if name == "afrProtectDeviationLambda" else 1
        new = "%.*f" % (digits, val)
        msq = replace_inner(msq, name, new)
        changes.append((name, old.strip(), new))

    for name, vals in CURVES.items():
        _, _, old, _ = grab(msq, name)
        msq = replace_inner(msq, name, fmt_axis(vals))
        changes.append((name, " ".join(old.split()), " ".join("%.1f" % v for v in vals)))

    # sanity: output must still be well-formed XML
    ET.fromstring(msq)

    with open(DST, "w") as f:
        f.write(msq)

    w = max(len(n) for n, _, _ in changes)
    print("Patched %d settings:" % len(changes))
    for name, old, new in changes:
        print("  %-*s  %s  ->  %s" % (w, name, old, new))
    print("\nWrote: %s" % DST)
    print("%s was NOT modified." % SRC)

if __name__ == "__main__":
    main()
