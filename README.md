# TurboExo

Tune, datalogs and commissioning notes for a 1999 Mazda Miata NB1 1.8 BP-4W with
an external TD04L-13T turbo and Speeduino UA4C (firmware 2025.01.7).

**September 28, 2026: sustained cold and warm idle established; current work is
idle control, throttle response and oil-pressure monitoring.** Four Toyota/Denso
COPs are installed (IGN1–4 → cylinders 1–3–4–2), with saved Wasted COP mode.
Stock red injectors are individually wired INJ1–4 → cylinders 1–4 and use
Semi-Sequential mode. Current wiring/I/O assignments are in
[docs/WIRING.md](docs/WIRING.md).

Start with [STATUS.md](STATUS.md) for current evidence, tune values and next
checks. [EXPERIMENT_LOG.md](EXPERIMENT_LOG.md) retains dated reasoning and
retracted hypotheses. [docs/REFERENCE.md](docs/REFERENCE.md) contains background
specifications; consult newer status entries for superseded statements.

## Files and workflow

- `CurrentTune.msq`: TunerStudio's working tune. Disk contents alone do not verify
  what is burned to the ECU.
- `restorePoints/`: automatic backups. August 29 19:22:11 is the stock-injector
  recovery baseline before COP changes. September 25 10:28:35 is a stale tune.
- `DataLogs/`: binary `.mlg` logs and converted `.csv` files, using Git LFS.
- `projectCfg/mainController.ini`: firmware-specific TunerStudio controls.
- `scripts/analyze_log.py`: first-pass analysis; its yellow-injector dead-time
  model is not appropriate for the currently installed stock injectors.

Snapshot before tuning, make a controlled change, open/burn it in TunerStudio,
power-cycle when required and confirm ECU readback. Log the result and update
the status and experiment history. Do not tune from short-crank AFR readings.

```sh
npx --yes mlg-converter --format=csv DataLogs/<file>.mlg
/opt/homebrew/bin/python3.12 scripts/analyze_log.py DataLogs/<file>.csv
```

Latest analyzed logs: `2026-09-28_13.09.03` (sustained run and throttle bog) and
`2026-09-28_13.29.24` (fully warm, closed-throttle idle only). Oil monitoring on
INP2/A9 and closed-loop IAC are staged on disk; consult STATUS.md for the newest
load file and whether ECU burn/readback has been confirmed.

Pi TSDash automatic logging was **disabled** at the September 25 live check.
Confirm recording before starting; do not rely on older automation notes.
