# AGENTS.md — TurboExo (Miata + Speeduino commissioning)

**What this repo is:** the tune, datalogs, and working notes for commissioning a
never-started build — a **1999 Mazda Miata NB1 1.8 (BP-4W, 1839 cc)** with an
external **TD04L-13T** turbo, running a **Speeduino UA4C (firmware 202501)** on
**speed-density**, wasted spark, paired injection. The engine ran fine before the
build; the build was **rewire + external turbo only** (internals known-good).

**Current objective:** get the first sustained idle. It cranks and briefly catches
but won't hold. Start at `STATUS.md` for the live front line; `EXPERIMENT_LOG.md`
is the full dated decision history (with deliberately-kept refuted hypotheses).

---

## Read before touching anything

These traps have repeatedly cost past sessions. Violating them wastes days.

1. **Do not tune fuel from logged AFR.** On short catches the Spartan wideband is
   still warming up and emits fixed cal voltages (**13.1–13.2**, sometimes ~16.5),
   and Speeduino echoes live O2 into *AFR Target* while `runSecs <= ego_sdelay`
   (`runSecs` resets every crank) — so **logged AFR mirrors AFR Target and is not
   mixture**. It's valid only after ~15 s+ of real exhaust heat. Until then, **read
   the plugs**. `scripts/analyze_log.py` prints the echo fraction so you can see it.
2. **reqFuel: use the right injectors.** This 1999 car's stock injector is the
   **238 cc "red"** (Denso 195500-3310); the installed **yellows are 425 cc**
   (Denso 195500-4450). From the GitHub-verified factory `reqFuel = 12.7`:
   `12.7 × 238/425 ≈ 7.0–7.1 ms` (fuel pressure cancels). **Do not use 265 cc** —
   that's the 01–05/94–97 injector, and it produced a wrong 7.9 (~13% rich).
3. **Factory-tune truth lives on GitHub** (`speeduino/Tunes`), **not the local
   Downloads copy** — that copy's `reqFuel` was hand-edited (12.7 → 14.7) and is
   corrupted. Always re-derive from the raw GitHub file.
4. **A single-cylinder symptom is hardware, not the tune.** Firing order
   **1-3-4-2**; injectors paired **1+4 / 2+3**; wasted-spark coils **1+4 / 2+3**.
   Cylinders in a pair get identical commanded fuel and spark. So if one fouls while
   its pair-mate is clean (e.g. **#2 sooty, #3 clean**), it's that cylinder's
   injector / coil tower / compression — the tune cannot fix it. (Confirmed: PW1=PW2
   to 0.000 ms in every log.)
5. **Battery gate.** A catch only "counts" if battery reaches **~13–14 V while
   firing** (alternator charging = the engine actually ran). Capped ~12 V never
   truly ran. Charge between attempts, ≤5 s cranks, dry plugs. The only genuine run
   so far (07-09, 1212 RPM) was the only session that hit 14 V.
6. **`veTable` idle-vacuum trap.** Rows = load (kPa, first row = lowest); columns =
   RPM (first col = 500). Forcing the idle-region cells' VE up (as the 07-10
   crank-VE/crank-wall edits did) makes the engine command ~2× fuel as MAP falls
   toward idle vacuum → it floods and can't settle, stuck near-atmospheric MAP. Keep
   idle cells at the last-known-good `TurboExo_VEfix_2026-07-09.msq` shape.
7. **Editing a `.msq` on disk does not reach the ECU.** TunerStudio owns
   `CurrentTune.msq`; changes take effect only when opened in TS and **burned**.
   Snapshot before edits (below). Change **one lever per test**.
8. **When unsure how Speeduino 202501 behaves, read the firmware source.** That's
   how the AFR echo (`sensors.cpp readO2()` / `corrections.cpp calculateAfrTarget()`)
   was resolved — don't guess at ECU internals.

---

## Analyze a datalog

```bash
# logs are binary .mlg; convert to semicolon CSV first
npx mlg-converter --format=csv DataLogs/<file>.mlg
python scripts/analyze_log.py DataLogs/<file>.csv
```

`analyze_log.py` reports duration, battery health + "truly ran?", sync, firing
rows, closed- vs cracked-throttle MAP, **effective fuel = PW − injOpen (0.9 ms)**
(the real delivered fuel), and the AFR-echo fraction. Judge fueling from **effective
fuel + plug reads**, never logged AFR.

## Change the tune

1. Snapshot: `cp CurrentTune.msq TurboExo_<desc>_<date>.msq` (TunerStudio also
   auto-saves to `restorePoints/`).
2. Edit in TunerStudio (or the `.msq` directly), minimal and one variable at a time.
3. **Burn to ECU** in TunerStudio (disk edits alone don't apply).
4. Add a dated entry to `EXPERIMENT_LOG.md` (change / hypothesis / result / verdict)
   and update `STATUS.md`.

---

## Repo map

- `CurrentTune.msq` — the live tune (on / going to the ECU).
- `TurboExo_*_<date>.msq` — milestone snapshots. **`TurboExo_VEfix_2026-07-09.msq`
  is the last-known-good** (only tune that self-sustained).
- `restorePoints/` — TunerStudio auto-backups (`.msq`, diffable history).
- `DataLogs/` — telemetry (`.mlg` raw + `.csv`), tracked via git-LFS.
- `dashboard/` — TunerStudio dashboards (`.dash`, git-LFS).
- `projectCfg/` — TunerStudio project files (`mainController.ini` = firmware definition).
- `EXPERIMENT_LOG.md` — chronological decision log (source of truth for *why*).
- `STATUS.md` — current loaded tune + next actions (start here for *what now*).
- `docs/REFERENCE.md` — pinned ground truth (specs, targets, verified-vs-open).
- `scripts/analyze_log.py` — datalog analyzer. `patch_commissioning_settings.py`,
  `generate_boost_tables.py` — existing tooling.
