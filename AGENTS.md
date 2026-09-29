# AGENTS.md — TurboExo (Miata + Speeduino commissioning)

**What this repo is:** the tune, datalogs, and working notes for commissioning a
running build — a **1999 Mazda Miata NB1 1.8 (BP-4W, 1839 cc)** with an
external **TD04L-13T** turbo, running a **Speeduino UA4C (firmware 202501)** on
**speed-density**, **four Toyota/Denso COPs in Wasted COP mode**, and
**Semi-Sequential injection**. The engine ran fine before the
build; the build was **rewire + external turbo only** (internals known-good).

**Current objective:** idle and running calibration; sustained cold and warm idle
were logged on 2026-09-28. Start at `STATUS.md` for the live front line; `EXPERIMENT_LOG.md`
is the full dated decision history (with deliberately-kept refuted hypotheses).

**Current ignition hardware (confirmed 2026-09-28):** four individual
Toyota/Denso **673-1300 / 90919-02239 coil-on-plug units**, replacing the original
Miata coil packs and plug leads. Documented wiring: **IGN1 → cylinder 1, IGN2 → 3,
IGN3 → 4, IGN4 → 2**. Saved `sparkMode` is **Wasted COP**; the earlier Sequential
setting is historical. COP describes the hardware; Wasted COP describes how the
ECU fires it. Do not apply stock Miata coil dwell/specifications to these COPs.

**Current wiring map:** `docs/WIRING.md`. INP1/A8 is Spartan status; INP2/A9
is assigned to the 0–100 psi oil-pressure transducer. Do not reuse either input.
Oil monitoring is configured on disk; burn/readback and physical verification are
tracked in STATUS.md. The OEM Spartan module has been replaced by a non-OEM unit.

---

## Routing

- **What now / latest tune to load:** start with [STATUS.md](STATUS.md).
- **Tune edits:** inspect `CurrentTune.msq` and recent `restorePoints/` before editing;
  compare actual constants, not filenames alone. Preserve newer TunerStudio saves.
  Disk contents do not prove ECU burn/readback.
- **Wiring / hardware / input assignments:** [docs/WIRING.md](docs/WIRING.md).
- **Specs / sensor manuals:** [docs/REFERENCE.md](docs/REFERENCE.md) and
  [docs/manuals/README.md](docs/manuals/README.md); current hardware supersedes old notes.
- **Why a change was made / prior tests:** [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md).
- **Run evidence:** `DataLogs/`; verify the latest file and use firmware source for
  ECU behavior. `FIRST_START_CHECKLIST.md` and `BOOST_TUNE_NOTES.md` are historical.

## Read before touching anything

These traps have repeatedly cost past sessions. Violating them wastes days.

1. **Do not tune fuel from logged AFR.** On short catches the Spartan wideband is
   still warming up and emits fixed cal voltages (**13.1–13.2**, sometimes ~16.5),
   and Speeduino echoes live O2 into *AFR Target* while `runSecs <= ego_sdelay`
   (`runSecs` resets every crank) — so **logged AFR mirrors AFR Target and is not
   mixture**. It's valid only after ~15 s+ of real exhaust heat. Until then, **read
   the plugs**. `scripts/analyze_log.py` prints the echo fraction so you can see it.
2. **reqFuel: use the right injectors.** Stock 238 cc reds are installed now
   (since 2026-07-19); reqFuel is 12.7 ms. The scaling below is historical.
   This 1999 car's stock injector is the
   **238 cc "red"** (Denso 195500-3310); the historical **yellows were 425 cc**
   (Denso 195500-4450). From the GitHub-verified factory `reqFuel = 12.7`:
   `12.7 × 238/425 ≈ 7.0–7.1 ms` (fuel pressure cancels). **Do not use 265 cc** —
   that's the 01–05/94–97 injector, and it produced a wrong 7.9 (~13% rich).
3. **Factory-tune truth lives on GitHub** (`speeduino/Tunes`), **not the local
   Downloads copy** — that copy's `reqFuel` was hand-edited (12.7 → 14.7) and is
   corrupted. Always re-derive from the raw GitHub file.
4. **Single-cylinder symptoms require output/hardware checks.** Firing order
   **1-3-4-2**; Semi-Sequential injection pairs **1+4 / 2+3** on individually wired
   injectors. Ignition uses four individual COPs (mapping above), not shared Miata
   coil towers. Check the affected cylinder's coil, plug, wiring/output mapping,
   injector and compression before changing global fuel. Equal logged PW channels
   do not prove every physical injector or coil is operating.
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
